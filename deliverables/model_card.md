# Model Card — FTW Field-Boundary Segmentation Model

Following Mitchell et al., *Model Cards for Model Reporting* (2019). This card documents the
pretrained **FTW `THREE_CLASS_FULL`** field-boundary model invoked in the tutorial (via
`ftw-tools` / `utils.download_and_run`), and — in a final subsection — the **RCF/MOSAIKS**
embedding step used for the crop-type use case. Facts below are read from the model checkpoint
metadata and from Kerner et al. (2025), arXiv:2409.16252.

## Model details

- **Task.** Semantic segmentation of Sentinel-2 imagery into a **per-pixel 3-class map** —
  *background*, field *boundary*, field *interior* — subsequently filtered by land cover and
  **polygonized** into vector field boundaries.
- **Architecture.** **U-Net** decoder with an **EfficientNet-B3** encoder/backbone
  (`num_filters=64`); **8 input channels** (two dated Sentinel-2 scenes × R/G/B/NIR); **3 output
  classes**.
- **Training config (from checkpoint metadata).** loss = cross-entropy; class weights
  `[0.04, 0.08, 0.88]` (background/boundary/interior — upweighting the rare interior/boundary
  classes); `ignore_index = 3`; `lr = 0.001`; backbone and decoder both trainable
  (`freeze_backbone = False`, `freeze_decoder = False`); `patience = 100`.
- **Checkpoint.** `THREE_CLASS_FULL` → `3_Class_FULL_FTW_Pretrained.ckpt`, downloaded via
  `ftw model download --type THREE_CLASS_FULL`. FTW also publishes other variants (e.g. a
  2-class model, and a version trained **only on CC-BY** sources for commercial use).
- **Developers / license.** FTW consortium (Kerner et al., 2025); distributed through
  `ftw-baselines` releases and the `ftw-tools` package. The `_FULL` checkpoint is trained on
  **all** benchmark sources, whose licenses vary — see the [datasheet](datasheet.md).

## Intended use

- **Primary uses.** Rapidly delineate *where cultivated fields likely are* from Sentinel-2, as a
  base layer for agricultural monitoring: crop-type mapping, cropped-area estimation, and
  change/anomaly detection over fields.
- **Intended users.** Researchers, agricultural-monitoring and MRV providers, NGOs, statistics
  offices, and policymakers who can pair outputs with local validation.
- **Out-of-scope / prohibited uses.** These polygons are **not** cadastral, legal, or ownership
  boundaries. Do **not** use them, on their own, to settle land tenure, allocate subsidies,
  underwrite insurance/credit for individual farmers, or enforce regulatory compliance; do **not**
  transplant the model to an unrepresented region without local labels and revalidation.

## Factors

Performance varies systematically with:
- **Region / geography** — training is **Europe-heavy**, so accuracy degrades under domain shift
  to under-represented regions (Africa, South/Southeast Asia).
- **Field size** — **smallholder** and irregular plots near the 10 m resolution limit are the most
  likely to be merged or missed.
- **Season / window choice** — the two contrasting-date windows must actually bracket the crop
  cycle; poor window selection weakens the signal.
- **Cloud cover & image quality** — the scene selector accepts up to 100 % cloud cover when
  nothing cleaner exists, which can corrupt inputs.

## Metrics

- **Pixel-level:** Intersection-over-Union (IoU), precision, recall on the boundary/interior
  classes.
- **Object-level:** precision and recall where a predicted field counts as correct only if it
  overlaps a ground-truth field with **IoU ≥ 0.5** (i.e., it penalizes over-/under-segmentation
  and merged fields, which pixel metrics can hide).

## Evaluation data

The **FTW benchmark** test splits (per-country 10 % test, blocked 3×3 split), plus **held-out
countries** (e.g. India, Cambodia, Vietnam, Ethiopia) for **zero-shot / transferability**
evaluation. See the [datasheet](datasheet.md).

## Training data

The **Fields of The World** benchmark — 70,462 Sentinel-2 chips with field-boundary masks
aggregated from ~26 source datasets across 24 countries / 4 continents (Europe-heavy). Full
provenance, licensing, and known gaps are in the [datasheet](datasheet.md).

## Quantitative analyses

Reported by Kerner et al. (2025) on the FTW benchmark (these are the paper's numbers — the
tutorial does **not** recompute IoU, as it has no ground-truth boundaries for the demo ROIs):
- **Pixel-level IoU** is fairly strong but region-dependent — roughly **0.59 (Slovenia)** up to
  **0.79 (France, South Africa)**.
- **Object-level** precision/recall are substantially lower — roughly **0.2–0.6** — reflecting
  merges, splits, and missed small fields.
- **Zero-shot** pixel IoU falls to **≈ 0.43** on a held-out region (Cambodia/Vietnam),
  quantifying the domain-shift penalty.

## Ethical considerations

- **Distributional harm.** Errors are **not** evenly distributed: smallholders and regions
  under-represented in training bear the highest error rates, so naïve operational use can
  systematically disadvantage the most vulnerable producers.
- **Misuse risk.** Treating model boundaries as authoritative could wrongly influence land-tenure,
  subsidy, insurance, or enforcement decisions.
- **Mitigation.** Foreground uncertainty, validate against local ground truth before acting, and
  keep a human (and domain/legal expertise) in the loop for any consequential decision.

## Caveats and recommendations

- Outputs come from **two single-date** Sentinel-2 snapshots (no multi-date compositing) and may
  be degraded by clouds — treat them as a **screening/prioritization** layer, not ground truth.
- For commercial use, prefer the **CC-BY-only** model variant to avoid non-commercially-licensed
  training data.
- **Validate locally** (ground truth or high-resolution imagery) before any regulatory, financial,
  or land-use decision. The tutorial demonstrates the workflow on a small ROI; it is **not** a
  production deployment.

---

## Embedding step: RCF / MOSAIKS (crop-type use case)

A second, lightweight "model" is used only to featurize fields for crop-type classification:

- **What it is.** **Random Convolutional Features (RCF / MOSAIKS)** via
  `utils.RCFWithCustomMaskPooling` (subclass of TorchGeo's `RCF`), configured
  `in_channels=8, features=256, kernel_size=3, seed=0, mode="gaussian"`. It applies **fixed,
  random** convolutional filters (ReLU of +conv and −conv), **mean-pools over the in-field
  pixels** of each polygon, and concatenates the responses into a **256-dimensional** embedding.
  There are **no trained/pretrained weights** — the filters are random and fixed by seed.
- **How it's used / evaluated.** Embeddings are standardized and fed to a **Logistic Regression**
  classifier in a deliberately **label-scarce** setting (stratified split, e.g. 10 % of fields for
  training, classes with < 10 fields dropped). Reported with **overall accuracy** and
  **macro-F1**, plus per-class precision/recall/F1 and a confusion matrix; a follow-on experiment
  sweeps the label budget to show accuracy rising then plateauing.
- **Intended use & limits.** A cheap, reproducible **feature extractor** for demonstrating
  few-label crop mapping — **not** a trained crop classifier. Crop labels here come from the
  **US-only USDA CDL**, so this pipeline must **not** be transplanted to another country without
  local labels, and must **not** drive individual-farmer subsidy/insurance/credit decisions.

---

References:
- FTW model & training (Kerner et al., 2025, AAAI-2025): https://arxiv.org/abs/2409.16252
- FTW datasheet (this tutorial): datasheet.md
- Model Cards for Model Reporting (Mitchell et al., 2019): https://arxiv.org/abs/1810.03993
- ftw-tools: https://github.com/fieldsoftheworld/ftw-tools · ftw-baselines: https://github.com/fieldsoftheworld/ftw-baselines
- MOSAIKS (Rolf et al., 2021, *Nature Communications*): https://www.nature.com/articles/s41467-021-24638-z
- TorchGeo RCF: https://torchgeo.readthedocs.io/
