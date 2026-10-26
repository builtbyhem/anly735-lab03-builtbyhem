```json
{
  "executed_utc": "2026-10-26T02:59:03.951971+00:00",
  "python": "3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]",
  "platform": "Linux-6.18.55-x86_64-with-glibc2.39",
  "packages": {
    "numpy": "2.3.5",
    "pandas": "2.2.3",
    "scikit-learn": "1.8.0",
    "scipy": "1.17.0",
    "matplotlib": "3.10.8",
    "Pillow": "12.3.0",
    "pyarrow": "26.0.0",
    "fsspec": "2026.9.0"
  },
  "configuration": {
    "dataset": "Camelyon17-WILDS v1.0 (PNG mirror)",
    "mirror": "wltjr1007/Camelyon17-WILDS",
    "revision": "d784d5344ba6c967f83f9f3d9b2f1e2a4d6eb78f",
    "sampling_seed": 735,
    "row_groups_per_train_shard": 8,
    "row_groups_per_validation_shard": 12,
    "row_groups_per_test_shard": 8,
    "development_centers": [
      0,
      3,
      4
    ],
    "ood_validation_center": 1,
    "ood_test_center": 2,
    "model": "StandardScaler + LogisticRegression",
    "C": 1.0,
    "solver": "lbfgs",
    "max_iter": 2000,
    "threshold": 0.5,
    "primary_metric": "accuracy",
    "secondary_metrics": [
      "balanced_accuracy",
      "roc_auc",
      "brier_score"
    ],
    "subgroups": [
      "class",
      "slide"
    ],
    "bootstrap_unit": "patient",
    "bootstrap_replicates": 1000,
    "bootstrap_seed": 8735,
    "selection_rule": "Fixed model and threshold; no validation or test-based model selection"
  },
  "hashes": {
    "data/features.parquet": "59f6ce8f9a327551479e796acd0362daa65adfcc87a900e51a3edb658ea0da5f",
    "data/sampling_manifest.json": "4ca4f22ccfca8509891d703007961e1cb89fda7ce62973f04c33482309b3fb90",
    "config/experiment.json": "ddfedc630d630e546c5cf836c7d7f0a3e828c980f6702e9129227a9ebe51c0ec",
    "code/prepare_data.py": "31c7181be4f085c5fb299c69eef92034dab6aa5c079f2854c2eeeebd47078934",
    "code/run_analysis.py": "673a7a79278c10438e7d77270e7e95dc8e5bee2f759f6ec8dd8b128bbf1d2d62"
  },
  "n_features": 88,
  "model_iterations": [
    330
  ],
  "fitted_models": 1
}
```
