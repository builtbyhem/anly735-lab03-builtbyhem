# Professor template and submission audit

The supplied Lab 3 instructions request one rendered Quarto HTML report. The general course template defaults to Word. Both formats are supplied from `replication-lab.qmd`; Lab 3’s HTML requirement takes precedence.

| Professor template item | Implementation |
| --- | --- |
| Study metadata | Article, authors, URL, replication type, environment, packages, seeds, repository |
| 1 Research Claim | Scoped hospital-shift claim and explicit research question |
| 2 Replication Strategy | Partial replication; retained elements and departures |
| 3 Data | Source, splits, sampling, provenance, environment table |
| 4 Method | Features, preprocessing, fixed classifier, metrics |
| 5 Results | Tables, two figures, class and slide diagnostics, uncertainty, diagnosis |
| 6 Compare | Original-versus-replication table, interpretation, deployment judgment |
| 7 Reproducibility Check | All nine checklist items, greatest challenge, limitations, commands |
| 8 Extend | One proposed, unexecuted hospital-holdout extension |
| Replication Verdict | Partially Reproduced selected and explained |
| References | APA citations and source list |
| Word rendering | Quarto DOCX output, Lab 2 style reference, deterministic layout script |
| Lab 3 rendering | Self-contained Quarto HTML; complete session record retained |

Section word counts in the general template are approximate guidance. Additional Lab 3 requirements are retained rather than removed to meet those suggested lengths. All eight Lab 3 questions and the five rubric categories are mapped in `REVIEW_CHECKLIST.md`.

The Lab 2 reference file supplies formatting conventions only. Its report content is not reused. The author name is Hemendra Gummadi, and all report repository links use `builtbyhem/anly735-lab03-builtbyhem`.

## Scope limitation

This submission uses sampled Camelyon17-WILDS images and a fixed image-feature logistic classifier. It does not rerun the published DenseNet or claim to execute an unavailable instructor-specific starter. These departures are explicit; the report should be assessed as a partial replication. The extension is proposed, not executed. This audit documents coverage and cannot guarantee a rubric score.
