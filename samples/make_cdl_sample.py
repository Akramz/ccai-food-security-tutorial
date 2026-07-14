## <- [GOAL] Build the tiny CDL clip shipped with the tutorial so fast mode avoids the
## >10 GB full-CONUS CDL download. Run once from the repo root, full CDL raster on disk:
##     python samples/make_cdl_sample.py
## Clips data/cdl/2023_30m_cdls.tif to the 14TPN crop-type ROI (native EPSG:5070,
## colormap + nodata preserved) and self-checks that the per-field majority-class
## join over the clip is byte-identical to the join over the full raster.
# REVIEW REQUIRED  (data integrity: this clip feeds the crop-type labels in fast mode)

import os

import geopandas as gpd
import numpy as np
import rasterio
import rasterio.mask
from rasterio.windows import Window, from_bounds

FULL = "data/cdl/2023_30m_cdls.tif"
BOUNDARIES = "ftw_boundaries_14TPN_summer_2023.gpkg"
OUT = "samples/cdl_14TPN_2023.tif"
MARGIN_M = 300  # ~10 CDL pixels of slack so all_touched masking stays inside the clip


def majority_class_vals(raster_path, fields_warped):
    ## Replicates the notebook's zonal-majority join (cell "majority_class_vals").
    vals = []
    with rasterio.open(raster_path) as f:
        for geom in fields_warped.geometry.values:
            out, _ = rasterio.mask.mask(
                f, [geom], crop=True, all_touched=True, nodata=0
            )
            out = out.squeeze().flatten()
            out = out[out != 0]
            u, c = np.unique(out, return_counts=True)
            vals.append(int(u[np.argmax(c)]))
    return np.array(vals)


def main():
    with rasterio.open(FULL) as src:
        fields = gpd.read_file(BOUNDARIES).to_crs(src.crs)
        minx, miny, maxx, maxy = fields.total_bounds
        ## Snap the window to integer pixel offsets on the SOURCE grid, else the clip is
        ## shifted <1 px and all_touched flips edge pixels (32/1112 fields drifted).
        w = from_bounds(minx - MARGIN_M, miny - MARGIN_M,
                        maxx + MARGIN_M, maxy + MARGIN_M, src.transform)
        col_off, row_off = int(np.floor(w.col_off)), int(np.floor(w.row_off))
        window = Window(col_off, row_off,
                        int(np.ceil(w.col_off + w.width)) - col_off,
                        int(np.ceil(w.row_off + w.height)) - row_off)
        data = src.read(1, window=window)
        profile = src.profile.copy()
        profile.update(height=data.shape[0], width=data.shape[1],
                       transform=src.window_transform(window),
                       compress="deflate", tiled=False)
        try:
            cmap = src.colormap(1)
        except ValueError:
            cmap = None

    with rasterio.open(OUT, "w", **profile) as dst:
        dst.write(data, 1)
        if cmap:
            dst.write_colormap(1, cmap)

    ## Parity gate: the clip must reproduce the full-raster join exactly, or it is junk.
    fields_warped = gpd.read_file(BOUNDARIES).to_crs(rasterio.open(OUT).crs)
    full_vals = majority_class_vals(FULL, fields_warped)
    clip_vals = majority_class_vals(OUT, fields_warped)
    n_diff = int((full_vals != clip_vals).sum())
    n = len(full_vals)
    assert n_diff == 0, f"clip join != full join for {n_diff} of {n} fields"
    kb = os.path.getsize(OUT) / 1e3
    h, w_px = data.shape
    print(f"{OUT}: {w_px}x{h} px, {kb:.0f} KB, parity OK over {n} fields")


if __name__ == "__main__":
    main()
