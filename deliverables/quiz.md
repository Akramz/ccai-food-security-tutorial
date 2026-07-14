# Quiz / Checkpoint Questions

Three questions (MCQ + true/false) covering learning objectives 2, 3, and 5. Also
delivered to CCAI by email. A collapsible-answer version is mirrored in the notebook near the
Final Discussion.

### Q1. After running the FTW model on a Sentinel-2 image, what does it output directly, and how do you get vector field polygons?
- A. Field polygons directly; no further steps are needed.
- B. A per-pixel 3-class segmentation mask (field / boundary / background), which is then filtered by land cover and polygonized into vector fields.
- C. A single crop-type label per tile, converted to polygons.
- D. A cloud-free mosaic that you digitize by hand.

**Answer:** B — FTW predicts a per-pixel segmentation raster, filtered then polygonized (`ftw inference polygonize`) into vectors. Checks Learning Objective 2.

### Q2. You increase `train_fraction` (share of fields used as labels) from 0.01 to 0.5 in the crop-type experiment. What best describes the effect on accuracy?
- A. It falls steadily as labels are added.
- B. It is unchanged; label count does not matter.
- C. It rises quickly at first, then largely plateaus (~40% of labels here).
- D. It is random until 100% of fields are labeled.

**Answer:** C — the labels-vs-accuracy sweep shows steep early gains that plateau, which is why few-label learning is viable. Checks Learning Objective 3.

### Q3. True or False: because the FTW model reaches pixel-level IoU up to ~0.79 in some countries, its per-field boundaries in your region are reliable enough to trigger a regulatory penalty (e.g., EUDR) without local validation.
- A. True
- B. False

**Answer:** B (False) — IoU varies by region and drops under domain shift (~0.43 zero-shot on held-out regions); object-level precision/recall are much lower (~0.2–0.6), and there is no local ground truth for your ROI. Checks Learning Objective 5.
