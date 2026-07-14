# `samples/` — small cached artifacts for fast mode

Tiny, pre-clipped data so the tutorial's **fast mode** (the notebook's `CONFIG["fast_mode"]`,
on by default) runs well under the 2-hour budget without large downloads.

## Contents

- **`cdl_14TPN_2023.tif`** (~51 KB) — USDA Cropland Data Layer (2023) clipped to the crop-type
  use-case ROI (MGRS tile **14TPN**, Iowa), in the native CDL CRS (EPSG:5070) with the CDL
  colormap preserved. Replaces the full-CONUS CDL download (**>10 GB**). `utils.ensure_cdl_sample()`
  returns this path in fast mode; `CONFIG["cdl_source"] = "full"` restores the TorchGeo download.
  Force-tracked past the repo-wide `*.tif` ignore (`git add -f`).
- **`make_cdl_sample.py`** — regenerates `cdl_14TPN_2023.tif` from the full raster. Run from the
  repo root with `data/cdl/2023_30m_cdls.tif` and `ftw_boundaries_14TPN_summer_2023.gpkg` present:
  ```bash
  python samples/make_cdl_sample.py
  ```
  It self-checks that the per-field majority-class join over the clip is **byte-identical** to the
  join over the full raster (parity gate), so fast mode and full mode produce the same crop labels.

## Notes

- The clip is keyed to **14TPN / 2023** (the hardcoded crop-type tile). If you change that tile,
  regenerate the clip; `ensure_cdl_sample()` will otherwise warn and fall back to the full CDL.
