# ANLY 735 Replication Laboratory 3: Camelyon17-WILDS

**Author:** Hemendra Gummadi  
**Repository:** https://github.com/builtbyhem/anly735-lab03-hemendra0329  
**Report:** [Rendered HTML](replication-lab.html) · [Quarto source](replication-lab.qmd)

This project supersedes the earlier Bike Sharing fallback. It is a **partial replication** using a fixed sampled Camelyon17 image cohort and a CPU-friendly image-statistics classifier. It is not a numerical reproduction of the published DenseNet baseline, and no instructor-specific starter is claimed.

## Reproduce the analysis offline

Use Python 3.12 and the recorded exact package versions:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python code/run_analysis.py
quarto render replication-lab.qmd --to html
```

On Windows, activate with `.venv\Scripts\activate`. Quarto 1.10.19 rendered the report. Jupyter is unnecessary; Python generates Markdown fragments, and Quarto includes them. The output HTML embeds its figures and styling.

`data/features.parquet` is a derived image-feature snapshot and includes labels, identifiers, grouping metadata, inclusion probabilities, source-row locations, and original PNG SHA-256 hashes. It contains no raw image bytes. It supports reproducing the statistical analysis without re-downloading the original images.

## Rebuild the features from pinned images

```bash
python code/prepare_data.py
python code/run_analysis.py
quarto render replication-lab.qmd --to html
```

The preparation step accesses the public Hugging Face PNG mirror at pinned revision d784d5344ba6c967f83f9f3d9b2f1e2a4d6eb78f. It reads sampled row groups through HTTP range requests and caches per-shard feature files. Up to six shard operations run concurrently; the sample remains deterministic regardless of completion order. `data/cache/` is optional and excluded from the deliverable archive. Remove that directory only if deliberately rebuilding features from source rather than reusing caches.

The official CodaLab archive returned HTTP 503 during preparation. The mirror is third-party. Matching counts, hospital metadata, patch dimensions and lossless PNG encoding establish consistency but not independently verified equivalence to the complete official archive. This limitation is explicit in the report.

## Fixed design

- Uniform row-group sampling within every source shard before model outcomes; seed 735.
- 8 groups per training shard, 12 per combined-validation shard, 8 per test shard.
- Source hospitals 0, 3, 4; target hospital 2. Hospital 1 (OOD validation) excluded.
- 11,200 train patches; 1,500 ID patches; 3,164 OOD patches.
- Whole-patch and central-region image statistics: 88 predictors, no metadata predictors.
- One fitted StandardScaler + logistic regression pipeline, C=1, lbfgs, max_iter=2000; fixed threshold 0.5.
- Primary accuracy, plus balanced accuracy, ROC AUC, Brier score, and class/slide diagnostics.
- Patient-cluster bootstrap, 1,000 replicates; explicitly conditional on one fitted model and sampled images.

The original `id_val` split is used only as an evaluation comparator, never to choose model settings or thresholds. Training and ID patches share source slides/patients by benchmark design. OOD patients and slides are disjoint. Exact image hash and coordinate overlap across splits is checked.

## Project structure

- `replication-lab.qmd`, `references.bib`, `styles.css`: report source and styling.
- `code/prepare_data.py`: fixed sampling and image-feature extraction.
- `code/run_analysis.py`: single fit, unchanged evaluations, tables, figures, metadata.
- `config/experiment.json`: decisions recorded before model evaluation.
- `data/features.parquet`, `data/sampling_manifest.json`: reproducible analytical inputs.
- `results/`: raw predictions, metrics, subgroup evidence, approximate intervals, diagnostics, hashes and verification.
- `vendor/`: snapshots of the official dataset implementation and configuration, retained as references rather than executed neural-model code.
- `REVIEW_CHECKLIST.md`: full assignment and rubric mapping.

Rerunning analysis overwrites generated outputs. The report is not a live computation engine; run the Python script before rendering it after any input/configuration change. Model changes would require reinterpreting the report, rather than retaining the existing narrative.

## Attribution and review

Cite Koh et al. (2021), the Camelyon17 source dataset, and the specified mirror. The official implementation describes the original images as CC0. Mirror-specific provenance is documented separately. Vendored WILDS code retains its MIT license.

The submission has not been uploaded to Canvas. This repository contains the completed Lab 3 materials; the first two lab repositories were not changed. AI assistance is disclosed in the report, and student review remains necessary.
