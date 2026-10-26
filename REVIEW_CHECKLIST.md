# Lab 3 review and requirement mapping

## Scope and status

The report now uses Camelyon17-WILDS rather than the earlier Bike Sharing fallback. Its partial-replication strategy is explicit: original hospital split logic and image task, a pinned third-party PNG mirror, sampled row groups, and a simplified CPU classifier. No numerical reproduction of DenseNet is claimed. No instructor-specific starter was identified; the implementation follows the supplied workflow and general course template rather than falsely claiming to execute a supplied notebook.

## All eight assignment questions

| Requirement | Where addressed |
| --- | --- |
| What distinguishes the environments? | Hospital codes, source versus held-out hospital, patients/slides, ID-validation caveat, environment table |
| How does performance change? | Accuracy, balanced accuracy, AUC, Brier, generated findings and figure |
| Which dimension changes most? | Specificity collapse and false-positive increase; avoids comparing incompatible metric units |
| Do subgroups differ? | Tumor versus non-tumor performance, full slide summaries and sample-size caveat |
| What evidence suggests explanations? | Near-constant prevalence, class-conditional errors, color statistics, full feature-shift audit |
| What can be concluded? | Fixed classifier deteriorates at the specified target hospital, concentrated in specificity |
| What cannot be concluded? | Causal staining explanation, arbitrary-hospital transport, DenseNet reproduction, clinical or demographic-fairness validity |
| What additional evidence is needed? | New patients/slides/hospitals, representative prevalence, intended use and tolerances, measurement checks, independent validation of revisions |

## Rubric mapping: 4 points each, 20 total

| Category | Included evidence |
| --- | --- |
| Research claim and strategy | One scoped claim, partial strategy justified, retained elements and departures explicit |
| Computational reproducibility and method | Pinned revision, source snapshot, manifest, image hashes, derived data, exact packages, code, fixed config, unchanged model, raw predictions, reproduction commands |
| Results, comparison, interpretation | Generated ID/OOD comparisons, class and slide analysis, uncertainty, original result and metric comparison, distinct replication verdict and deployment judgment |
| Critical reproducibility evaluation and extension | Mirror provenance, sampling design, shared source slides, simple representation, single target hospital, artificial prevalence, uncertainty limits; one concrete leave-one-hospital-out extension |
| Communication and transparency | Rendered embedded Quarto HTML, labeled figures and tables, source citations, explicit unsupported claims and assistance disclosure |

## Verification completed

The following were verified computationally:

- Every predictor is an image statistic; metadata and outcomes are excluded.
- Coordinates are unique; exact image hashes do not cross splits.
- Training and ID use hospitals 0, 3, 4; OOD uses hospital 2.
- OOD validation hospital 1 is excluded.
- Target patients and slides are absent from development.
- All three source hospitals and all 30 source slides are represented; target includes all 10 slides.
- Both classes occur in each analysis split.
- The optimizer converged; one pipeline was fitted and evaluated unchanged twice.
- A second run produced identical row-level predictions.
- Accuracy and Brier were independently reconciled with raw predictions.
- All 21 mirror shards appear in the sampling frame; full shard counts match the original documented counts.
- Patient-bootstrap undefined class-specific replicates are counted and disclosed (992 valid balanced-accuracy replicates in OOD, 1,000 for accuracy/Brier).

Machine-readable results: `results/verification.json`, `results/html_verification.json`, `results/session.json`.

## Important interpretation checks

- `id_val` is explicitly identified; it is never called an official untouched ID test set.
- Source training and ID share patients/slides by original design; this limits new-slide generalization claims.
- Third-party mirror consistency checks do not establish bitwise equivalence to the unavailable official archive.
- No neural model or robustness algorithm was rerun; partial-replication language is retained throughout.
- Bootstrap intervals do not estimate variability across possible target hospitals or fully capture row-group design uncertainty.
- Roughly 50/50 research prevalence is not assumed to represent clinical prevalence.
- The extension is proposed, not reported as executed.
- Student review and Canvas submission have not been claimed.

## Packaging

The standalone HTML is the Lab 3 report deliverable. A matching Quarto-rendered DOCX is also included, using the general professor template structure and Lab 2 style reference. The project archive includes Quarto source, code, exact dependencies, input feature snapshot, sampling manifest, results, and source references. It excludes transient per-shard caches and unused intermediate downloads. The snapshot permits offline analytical reproduction; full image-feature regeneration requires network access to the pinned mirror.

The completed materials are published at https://github.com/builtbyhem/anly735-lab03-builtbyhem. The first two lab repositories were not changed, and nothing was submitted to Canvas.
