"""Fit once on sampled training images; evaluate unchanged on ID and OOD.

The bundled feature snapshot supports offline analytical reproduction. Run
prepare_data.py separately to regenerate features from the pinned PNG mirror.
"""
from pathlib import Path
import hashlib
import importlib.metadata as im
import json
import platform
import sys
from datetime import datetime, timezone

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, brier_score_loss, roc_auc_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'config/experiment.json').read_text())
OUT = ROOT/'results'
OUT.mkdir(exist_ok=True)
data = pd.read_parquet(ROOT/'data/features.parquet')
features = [c for c in data if c.startswith(('full_', 'center_'))]
train = data[data.split=='train'].copy()
tests = data[data.split.isin(['ID', 'OOD'])].copy()
checks = {}
checks['features_are_88_image_statistics_only'] = len(features)==88
keys = ['patient', 'node', 'x_coord', 'y_coord']
checks['all_image_coordinates_unique'] = not data.duplicated(keys).any()
checks['no_missing_features_or_labels'] = not data[features+['label']].isna().any().any()
checks['training_hospitals_correct'] = set(train.center)==set(CFG['development_centers'])
checks['ID_hospitals_correct'] = set(tests[tests.split=='ID'].center)==set(CFG['development_centers'])
checks['OOD_hospital_correct'] = set(tests[tests.split=='OOD'].center)=={CFG['ood_test_center']}
checks['OOD_validation_excluded'] = CFG['ood_validation_center'] not in set(data.center)
checks['OOD_patients_unseen'] = set(data[data.split!='OOD'].patient).isdisjoint(tests[tests.split=='OOD'].patient)
checks['OOD_slides_unseen'] = set(data[data.split!='OOD'].slide).isdisjoint(tests[tests.split=='OOD'].slide)
checks['both_classes_in_each_split'] = all(set(g.label)=={0,1} for _,g in data.groupby('split'))
assert all(checks.values()), checks
model = Pipeline([('scale', StandardScaler()), ('model', LogisticRegression(
    C=CFG['C'], solver=CFG['solver'], max_iter=CFG['max_iter']))])
# Inverse row-group inclusion probabilities correct any small shard differences.
model.fit(train[features], train.label, model__sample_weight=1/train.inclusion_probability)
assert model['model'].n_iter_.max()<CFG['max_iter'], 'Optimizer did not converge'
tests['probability'] = model.predict_proba(tests[features])[:,1]
tests['prediction'] = (tests.probability>=CFG['threshold']).astype(int)
tests['weight'] = 1/tests.inclusion_probability
predcols = ['split','label','prediction','probability','weight','center','patient','slide','image_id',
    'source_shard','row_group','row_in_shard','image_sha256']
tests[predcols].to_csv(OUT/'predictions.csv', index=False)

def evaluate(g):
    w = g.weight.to_numpy()
    return {'n':len(g), 'accuracy':accuracy_score(g.label,g.prediction,sample_weight=w),
        'balanced_accuracy':balanced_accuracy_score(g.label,g.prediction,sample_weight=w),
        'roc_auc':roc_auc_score(g.label,g.probability,sample_weight=w),
        'brier':brier_score_loss(g.label,g.probability,sample_weight=w),
        'log_loss':log_loss(g.label,g.probability,sample_weight=w),
        'prevalence':np.average(g.label,weights=w)}

metrics = pd.DataFrame([{'environment':e, **evaluate(g)} for e,g in tests.groupby('split')])
metrics.to_csv(OUT/'metrics.csv',index=False)
groups=[]
for field in ['label','slide','center']:
    for (e,value),g in tests.groupby(['split',field]):
        groups.append({'environment':e,'variable':field,'value':value,'n':len(g),
            'accuracy':np.average(g.label==g.prediction,weights=g.weight),
            'mean_probability':np.average(g.probability,weights=g.weight)})
subgroups=pd.DataFrame(groups)
subgroups.to_csv(OUT/'subgroup_metrics.csv',index=False)
envs=pd.DataFrame([{'split':e,'n':len(g),'hospitals':','.join(map(str,sorted(g.center.unique()))),
    'patients':g.patient.nunique(),'slides':g.slide.nunique(),'tumor_fraction':g.label.mean(),
    'weighted_tumor_fraction':np.average(g.label,weights=1/g.inclusion_probability),
    'mean_red':g.center_r_mean.mean(),'mean_green':g.center_g_mean.mean(),'mean_blue':g.center_b_mean.mean()}
    for e,g in data.groupby('split')])
envs.to_csv(OUT/'environments.csv',index=False)
id_x=data[data.split=='ID'];ood_x=data[data.split=='OOD']
shift=pd.DataFrame([{'feature':f,'ID_mean':id_x[f].mean(),'OOD_mean':ood_x[f].mean(),
    'standardized_difference':(ood_x[f].mean()-id_x[f].mean())/train[f].std()}
    for f in features if train[f].std()>0])
shift.to_csv(OUT/'feature_shift.csv',index=False)

# Cluster bootstrap conditions on one trained model and the selected images.
rng=np.random.default_rng(CFG['bootstrap_seed']);boots={}
for e,g in tests.groupby('split'):
    q=g.assign(n=g.weight,correct=g.weight*(g.label==g.prediction),
        sq=g.weight*(g.probability-g.label)**2,
        n0=g.weight*(g.label==0),c0=g.weight*(g.label==0)*(g.prediction==0),
        n1=g.weight*(g.label==1),c1=g.weight*(g.label==1)*(g.prediction==1))
    a=q.groupby('patient')[['n','correct','sq','n0','c0','n1','c1']].sum().to_numpy()
    idx=rng.integers(0,len(a),size=(CFG['bootstrap_replicates'],len(a)))
    z=a[idx].sum(axis=1)
    specificity=np.divide(z[:,4],z[:,3],out=np.full(len(z),np.nan),where=z[:,3]>0)
    sensitivity=np.divide(z[:,6],z[:,5],out=np.full(len(z),np.nan),where=z[:,5]>0)
    boots[e]=np.column_stack([z[:,1]/z[:,0], .5*(specificity+sensitivity), z[:,2]/z[:,0]])
cis=[]
for j,k in enumerate(['accuracy','balanced_accuracy','brier']):
    for name,v in [('ID',boots['ID'][:,j]),('OOD',boots['OOD'][:,j]),('OOD minus ID',boots['OOD'][:,j]-boots['ID'][:,j])]:
        low,high=np.quantile(v[np.isfinite(v)],[.025,.975])
        cis.append({'metric':k,'condition':name,'lower':low,'upper':high,
            'valid_replicates':int(np.isfinite(v).sum()),'requested_replicates':CFG['bootstrap_replicates']})
ci=pd.DataFrame(cis);ci.to_csv(OUT/'patient_bootstrap_intervals.csv',index=False)
checks['model_converged']=True
checks['one_model_fitted']=True
checks['ID_and_OOD_predictions_complete']=len(tests)==len(data[data.split!='train'])
checks['no_exact_image_hash_overlap_between_splits']=data.groupby('image_sha256').split.nunique().max()==1
checks={k:bool(v) for k,v in checks.items()}
assert all(checks.values()),checks
(OUT/'verification.json').write_text(json.dumps(checks,indent=2))
versions={p:im.version(p) for p in ['numpy','pandas','scikit-learn','scipy','matplotlib','Pillow','pyarrow','fsspec']}
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
    [ROOT/'data/features.parquet',ROOT/'data/sampling_manifest.json',ROOT/'config/experiment.json',
     ROOT/'code/prepare_data.py',ROOT/'code/run_analysis.py']}
meta={'executed_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),
    'packages':versions,'configuration':CFG,'hashes':hashes,'n_features':len(features),
    'model_iterations':model['model'].n_iter_.tolist(),'fitted_models':1}
(OUT/'session.json').write_text(json.dumps(meta,indent=2))
(ROOT/'requirements.txt').write_text('\n'.join(f'{p}=={v}' for p,v in versions.items())+'\n')

def md_table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
        ['| '+' | '.join(map(str,row))+' |' for row in rows])+'\n'

def write_table(name,headers,rows):
    (OUT/name).write_text(md_table(headers,rows))

m=metrics.set_index('environment')
write_table('environment_table.md',['Environment','Patches','Hospitals','Patients','Slides','Tumor (%)'],
    [[r.split,r.n,r.hospitals,r.patients,r.slides,f'{100*r.weighted_tumor_fraction:.1f}'] for r in envs.itertuples()])
write_table('performance_table.md',['Measure','ID','OOD','Change (OOD minus ID)'],
    [[label,f'{scale*m.loc["ID",k]:.{digits}f}{suffix}',f'{scale*m.loc["OOD",k]:.{digits}f}{suffix}',
      f'{scale*(m.loc["OOD",k]-m.loc["ID",k]):+.{digits}f}'+(' pp' if scale==100 else '')]
      for k,label,scale,digits,suffix in [('accuracy','Accuracy',100,2,'%'),
      ('balanced_accuracy','Balanced accuracy',100,2,'%'),('roc_auc','ROC AUC',1,3,''),('brier','Brier score',1,3,'')]])
write_table('class_table.md',['Class / measure','ID patches','ID performance','OOD patches','OOD performance','Change'],
    [[label,int(a.n),f'{100*a.accuracy:.2f}%',int(b.n),f'{100*b.accuracy:.2f}%',f'{100*(b.accuracy-a.accuracy):+.2f} pp']
     for value,label in [(0,'Non-tumor / specificity'),(1,'Tumor / sensitivity')]
     for a in [subgroups[(subgroups.environment=='ID')&(subgroups.variable=='label')&(subgroups.value==value)].iloc[0]]
     for b in [subgroups[(subgroups.environment=='OOD')&(subgroups.variable=='label')&(subgroups.value==value)].iloc[0]]])
write_table('interval_table.md',['Measure','ID 95% interval','OOD 95% interval','Difference 95% interval'],
    [[label]+[f'[{scale*r.lower:.2f}, {scale*r.upper:.2f}]'+(' pp' if e=='OOD minus ID' and scale==100 else '%' if scale==100 else '')
      for e in ['ID','OOD','OOD minus ID'] for r in ci[(ci.metric==k)&(ci.condition==e)].itertuples()]
      for k,label,scale in [('accuracy','Accuracy',100),('balanced_accuracy','Balanced accuracy',100),('brier','Brier',1)]])
write_table('slide_table.md',['Environment','Slides','Minimum slide accuracy','Median slide accuracy','Maximum slide accuracy'],
    [[e,len(g),f'{100*g.accuracy.min():.1f}%',f'{100*g.accuracy.median():.1f}%',f'{100*g.accuracy.max():.1f}%']
      for e,g in subgroups[subgroups.variable=='slide'].groupby('environment')])
write_table('color_table.md',['Center-patch feature','ID mean','OOD mean','Difference / training SD'],
    [[r.feature,f'{r.ID_mean:.3f}',f'{r.OOD_mean:.3f}',f'{r.standardized_difference:+.2f}']
     for r in shift[shift.feature.isin(['center_r_mean','center_g_mean','center_b_mean'])].itertuples()])
accdiff=100*(m.loc['OOD','accuracy']-m.loc['ID','accuracy'])
balancediff=100*(m.loc['OOD','balanced_accuracy']-m.loc['ID','balanced_accuracy'])
aucdiff=m.loc['OOD','roc_auc']-m.loc['ID','roc_auc']
brierdiff=m.loc['OOD','brier']-m.loc['ID','brier']
text=(f'Accuracy changed from **{100*m.loc["ID","accuracy"]:.2f}% to {100*m.loc["OOD","accuracy"]:.2f}%**, '
    f'a difference of {accdiff:+.2f} percentage points. Balanced accuracy changed by {balancediff:+.2f} points, '
    f'ROC AUC by {aucdiff:+.3f}, and Brier score by {brierdiff:+.3f}. '
    'Higher accuracy, balanced accuracy, and AUC are better; lower Brier score is better.\n')
(OUT/'findings.md').write_text(text)
(OUT/'session_block.md').write_text('```json\n'+json.dumps(meta,indent=2)+'\n```\n')
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,3,figsize=(10,3.6),constrained_layout=True)
for ax,k,title,scale in zip(axes,['accuracy','roc_auc','brier'],['Accuracy (%)','ROC AUC','Brier score'],[100,1,1]):
    v=m.loc[['ID','OOD'],k]*scale
    ax.bar(['Familiar hospitals','Held-out hospital'],v,color=['#267b8a','#c46e47'],width=.6)
    ax.set_title(title);ax.set_ylim(0,100 if scale==100 else 1 if k=='roc_auc' else max(v)*1.3)
    ax.tick_params(axis='x',labelsize=8)
    for i,value in enumerate(v):ax.annotate(f'{value:.2f}',(i,value),xytext=(0,5),textcoords='offset points',ha='center')
fig.savefig(OUT/'performance.png',dpi=170,bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(7,4),constrained_layout=True)
for e,color in [('ID','#267b8a'),('OOD','#c46e47')]:
    g=subgroups[(subgroups.variable=='slide')&(subgroups.environment==e)].sort_values('accuracy')
    ax.plot(np.arange(1,len(g)+1),100*g.accuracy,'o-',label=e,color=color,alpha=.85)
ax.set(xlabel='Slide rank within each environment (not matched slides)',ylabel='Accuracy (%)',ylim=(0,100))
ax.legend(frameon=False);fig.savefig(OUT/'slide_performance.png',dpi=170,bbox_inches='tight');plt.close(fig)
print(metrics.to_string(index=False));print(envs.to_string(index=False))
print(subgroups[subgroups.variable=='label'].to_string(index=False))
print('Iterations:',model['model'].n_iter_);print('All checks:',checks)
