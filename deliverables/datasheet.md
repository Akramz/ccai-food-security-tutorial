# Datasheet — Fields of The World (FTW)

Following Gebru et al., *Datasheets for Datasets* (2021). This datasheet documents the **Fields
of The World (FTW)** benchmark dataset that the tutorial's field-boundary model is trained on,
plus the **auxiliary datasets** the tutorial layers on top (Sentinel-2 imagery, crop calendars,
USDA CDL crop labels, Hansen/GLAD forest-loss). Primary source: Kerner et al. (2025),
*Fields of The World: A Machine Learning Benchmark Dataset for Global Agricultural Field
Boundary Segmentation*, AAAI-2025 (AI for Social Impact track), arXiv:2409.16252.

## Motivation

- **Why was the dataset created?** To enable and benchmark **global** agricultural
  field-boundary segmentation from satellite imagery. Field boundaries are a foundational input
  for agricultural monitoring — crop-type mapping, area/yield estimation, and change detection —
  yet before FTW, labeled boundary data was fragmented, region-specific, and small. FTW is "an
  order of magnitude larger than previous datasets" and is explicitly aimed at
  climate-, food-security-, and development-relevant monitoring where field-level information is
  scarce.
- **Who created it?** The FTW consortium led by Hannah Kerner (Arizona State University) with
  collaborators across academia, industry, and the AI-for-Good community (see the paper's author
  list and the notebook's *Authors* section).
- **Funding / support.** Assembled from public and open datasets; see the paper's
  acknowledgements. The tutorial does not add new funding claims.

## Composition

- **What does an instance represent?** One **256 × 256-pixel** Sentinel-2 chip (10 m/pixel,
  ≈ 2.56 × 2.56 km on the ground) paired with **instance** and **semantic segmentation** masks of
  the agricultural fields it contains. The semantic mask has **3 classes** used by the model in
  this tutorial: *background*, field *boundary*, and field *interior*.
- **How many instances?** **70,462 samples** spanning **24 countries** across **4 continents**
  (Europe, Africa, Asia, South America). Coverage is **Europe-heavy** — most samples come from
  European countries with mature open field-parcel registries.
- **What data does each instance contain?** Per sample, two **contrasting-date** Sentinel-2 L2A
  scenes (**Window A** and **Window B**, e.g. planting/green-up vs. harvest/senescence), each
  with 4 bands — **red (B04), green (B03), blue (B02), near-infrared (B08)**. Stacked, this is the
  **8-band** input the tutorial feeds to the model. Labels are geo-referenced field polygons
  rasterized into the boundary/interior masks.
- **Is anything missing / are labels incomplete?** Yes. FTW targets **annual crops** and
  excludes perennial crops, orchards, pasture, and non-agricultural land. Some countries provide
  **presence-only** labels (fields are labeled where known, but absence of a label does not
  guarantee absence of a field), so recall estimates in those regions are optimistic.
- **Splits.** Per-country **80 % train / 10 % validation / 10 % test**, drawn with a **blocked
  (3 × 3 grid) random split** to limit spatial-autocorrelation leakage between adjacent chips.
  Separately, entire **held-out countries** (e.g. India, Cambodia, Vietnam, Ethiopia) support
  **zero-shot / transferability** evaluation.

## Collection process

- **How were the labels acquired?** FTW **aggregates and standardizes ~26 pre-existing datasets**
  found through "a comprehensive search for field polygons from government databases, published
  literature, and other websites." Sources include national/EU agricultural registries (e.g.
  Austria, Denmark, France) and research datasets (e.g. EuroCrops, Planet/Radiant Earth, NASA
  Harvest). The FTW authors **did not hand-label** fields; they harmonized existing annotations to
  a common schema (the **fiboa** field-boundary specification).
- **How was the imagery acquired?** Sentinel-2 L2A scenes matched to each labeled region and to
  the two seasonal windows; in this tutorial the imagery is pulled at runtime from the
  **Microsoft Planetary Computer** STAC catalog.
- **Over what timeframe?** Labels reflect the reference year of each source registry; imagery is
  matched to those years. Exact per-source years vary — see the paper's Table 1.

## Preprocessing / cleaning / labeling

- Source polygons were reprojected, deduplicated, and harmonized to the fiboa spec, then
  **rasterized** into the 3-class semantic masks; the explicit **boundary** class is derived from
  polygon edges so that adjacent touching fields do not merge.
- Sentinel-2 windows are chosen to be **contrasting** in the crop calendar (green-up vs.
  senescence), which the model exploits to separate cultivated fields from surroundings. In the
  tutorial, window dates come from a global **crop-calendar** raster (`utils.download_crop_calendars`)
  and the lowest-cloud scenes are selected (escalating the cloud threshold up to 100 % if nothing
  cleaner exists).

## Uses

- **What is the dataset for?** Training and benchmarking field-boundary segmentation; transfer
  learning to new regions; region-specific evaluation; downstream agricultural monitoring
  (crop-type mapping, area estimation) and climate/food-security/sustainable-development
  applications.
- **What should it *not* be used for?** The resulting boundaries are **not** cadastral, legal, or
  ownership boundaries and must not, on their own, settle land tenure, allocate subsidies, or
  enforce compliance. Because coverage is Europe-heavy and some regions are presence-only,
  models trained on FTW **transfer unevenly**; errors fall hardest on **smallholders** with small
  or irregular plots. Any high-stakes (regulatory, financial, land-use) decision requires local
  ground truth and revalidation first.

## Distribution

- **How is it distributed?** Openly, via **Source Cooperative**
  (`source.coop/kerner-lab/fields-of-the-world`); code and pretrained models via
  **`ftw-baselines`** (github.com/fieldsoftheworld/ftw-baselines) and the **`ftw-tools`** CLI;
  data loaders via **TorchGeo**.
- **License.** FTW **inherits the licenses of its ~26 constituent source datasets**, which
  **vary** (some permit commercial use, some do not). Because of this, the project ships a model
  variant trained **only on openly (CC-BY) licensed** sources for users who need to avoid
  non-commercial data — the tutorial otherwise uses the `THREE_CLASS_FULL` model trained on all
  sources. Check the per-source license before commercial reuse.

## Maintenance

- **Maintainer / contact.** The FTW consortium; primary contact **Hannah Kerner**
  (hkerner@asu.edu, Arizona State University).
- **Versioning / updates.** Distributed and versioned through Source Cooperative and the
  `ftw-baselines` releases; the benchmark may be extended with additional countries over time.

---

## Auxiliary datasets used in this tutorial

These are **not** part of FTW but are joined to FTW-derived boundaries in the two use cases.

| Dataset | Role | Provenance & resolution | Key caveat |
|---|---|---|---|
| **Sentinel-2 L2A** (Windows A/B) | Model input (8 bands = 2 × RGB+NIR) | ESA/Copernicus via Microsoft Planetary Computer; 10 m | Two single-date snapshots per season (no compositing); cloud threshold escalates to 100 % if needed. |
| **Global crop calendars** | Pick the two seasonal windows | `ftw-qgis-plugin` global crop-calendar rasters | Coarse 3×3° grid; a single start/end-of-season per tile center. |
| **USDA Cropland Data Layer (CDL)** | Crop-type labels for the crop-mapping use case | USDA NASS annual raster from Landsat/Sentinel-2 + NASS/FSA ground truth; 30 m (recently 10 m) | **Continental US only**; annual; must not drive individual-farmer subsidy/insurance/credit decisions. |
| **Hansen / GLAD Global Forest Change** (`lossyear`) | Forest-loss overlay for the forest-monitoring use case | UMD/GLAD, `GFC-2024-v1.12`, `lossyear` layer; 30 m, 10°×10° granules | Flags **tree-cover loss ≠ deforestation** and not its cause; 30 m pixels often larger than a field; misses pre-2000 loss. Descriptive overlay, not a model prediction. |

---

References:
- Kerner et al. (2025), *Fields of The World* (AAAI-2025, AISI track): https://arxiv.org/abs/2409.16252
- FTW dataset (Source Cooperative): https://source.coop/repositories/kerner-lab/fields-of-the-world/
- Fields of The World: https://fieldsofthe.world/ · https://github.com/fieldsoftheworld
- fiboa field-boundary specification: https://github.com/fiboa
- Datasheets for Datasets (Gebru et al., 2021): https://arxiv.org/abs/1803.09010
- USDA Cropland Data Layer: https://www.nass.usda.gov/Research_and_Science/Cropland/SARS1a.php
- UMD GLAD/Hansen Global Forest Change: https://storage.googleapis.com/earthenginepartners-hansen/GFC-2024-v1.12/download.html
