"""Rebuild the pinned sampled-image feature snapshot. Network required.

Select entire Parquet row groups, uniformly without replacement within each
shard, before reading labels or fitting a model. Record every sampled row.
The mirror combines ID and OOD validation; center metadata separates them.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import io
import json
import time
import urllib.request

import fsspec
import numpy as np
import pandas as pd
from PIL import Image
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config/experiment.json").read_text())
CACHE = ROOT / "data/cache"
CACHE.mkdir(parents=True, exist_ok=True)
API = f"https://huggingface.co/api/datasets/{CFG['mirror']}/tree/{CFG['revision']}?recursive=true"
FILES = json.load(urllib.request.urlopen(API, timeout=40))
SHARDS = [x for x in FILES if x['path'].endswith('.parquet')]

def image_features(blob):
    img = Image.open(io.BytesIO(blob))
    if img.format != 'PNG' or img.size != (96, 96):
        raise ValueError(f"Unexpected mirror encoding: {img.format}, {img.size}")
    a = np.asarray(img.convert('RGB'), dtype=np.float64) / 255.0
    vals, names = [], []
    for region, x in [('full', a), ('center', a[32:64, 32:64])]:
        for c, channel in enumerate(['r', 'g', 'b']):
            z = x[:, :, c]
            stats = [z.mean(), z.std(), *np.quantile(z, [.1, .5, .9])]
            hist = np.histogram(z, bins=np.linspace(0, 1, 9))[0] / z.size
            vals.extend([*stats, *hist])
            names.extend([f'{region}_{channel}_{s}' for s in ['mean', 'sd', 'q10', 'q50', 'q90']]
                + [f'{region}_{channel}_hist{j}' for j in range(8)])
        gray = .299*x[:, :, 0] + .587*x[:, :, 1] + .114*x[:, :, 2]
        vals.extend([np.abs(np.diff(gray, axis=0)).mean(), np.abs(np.diff(gray, axis=1)).mean(),
            (gray < .25).mean(), (gray < .5).mean(), (gray < .75).mean()])
        names.extend([f'{region}_{s}' for s in ['gradient_y', 'gradient_x', 'dark25', 'dark50', 'dark75']])
    return vals, names

def process_shard(entry):
    path = entry['path']
    cached = CACHE / (Path(path).stem + '.features.parquet')
    log_file = cached.with_suffix('.json')
    if cached.exists() and log_file.exists():
        return pd.read_parquet(cached), json.loads(log_file.read_text())
    kind = Path(path).name.split('-')[0]
    count = CFG[f'row_groups_per_{kind}_shard']
    seed = int.from_bytes(hashlib.sha256(f"{CFG['sampling_seed']}:{path}".encode()).digest()[:8], 'little')
    url = f"https://huggingface.co/datasets/{CFG['mirror']}/resolve/{CFG['revision']}/{path}"
    records = []
    fs = fsspec.filesystem('https', client_kwargs={'trust_env': True})
    with fs.open(url, 'rb', size=entry['size'], block_size=262144, cache_type='bytes') as handle:
        pf = pq.ParquetFile(handle)
        rng = np.random.default_rng(seed)
        groups = sorted(rng.choice(pf.num_row_groups, min(count, pf.num_row_groups), replace=False).tolist())
        offsets = np.cumsum([0] + [pf.metadata.row_group(i).num_rows for i in range(pf.num_row_groups)])
        for group in groups:
            rows = pf.read_row_group(group).to_pylist()
            for k, row in enumerate(rows):
                center = int(row['center'])
                split = ('train' if kind == 'train' else 'OOD' if kind == 'test'
                    else 'OOD_validation' if center == CFG['ood_validation_center'] else 'ID')
                # OOD validation is deliberately excluded from this fixed-model study.
                if split == 'OOD_validation':
                    continue
                blob = row['image']['bytes']
                values, names = image_features(blob)
                record = {key: row[key] for key in ['label', 'center', 'image_id', 'patient', 'node', 'x_coord', 'y_coord', 'slide']}
                record.update(dict(zip(names, values)))
                record.update(split=split, source_shard=path, row_group=group,
                    row_in_shard=int(offsets[group]+k), image_sha256=hashlib.sha256(blob).hexdigest(),
                    inclusion_probability=len(groups)/pf.num_row_groups)
                records.append(record)
            print(f'{Path(path).name}: group {group}, cumulative {len(records)} images', flush=True)
        log = {'path': path, 'source_rows': pf.metadata.num_rows, 'source_row_groups': pf.num_row_groups,
            'selected_row_groups': groups, 'selection_seed': seed, 'retained_rows': len(records),
            'inclusion_probability': len(groups)/pf.num_row_groups}
    frame = pd.DataFrame(records)
    frame.to_parquet(cached, index=False)
    log_file.write_text(json.dumps(log, indent=2))
    return frame, log

frames, logs = [], []
with ThreadPoolExecutor(max_workers=6) as executor:
    futures = {executor.submit(process_shard, entry): entry for entry in SHARDS}
    for future in as_completed(futures):
        frame, log = future.result()
        frames.append(frame)
        logs.append(log)
        print('Finished', log['path'], flush=True)
out = pd.concat(frames, ignore_index=True).sort_values(['split', 'source_shard', 'row_in_shard']).reset_index(drop=True)
out.to_parquet(ROOT / 'data/features.parquet', index=False)
(ROOT / 'data/sampling_manifest.json').write_text(json.dumps(sorted(logs, key=lambda d: d['path']), indent=2))
print(out.groupby(['split', 'center', 'label']).size().to_string(), flush=True)
