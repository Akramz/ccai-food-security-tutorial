import json
import math
import os
import subprocess
import urllib.request
from datetime import datetime, timedelta

import ipywidgets as widgets
import leafmap
import planetary_computer
import pystac_client
import rasterio
import torch
import torch.nn.functional as F
from ipyleaflet import GeoJSON
from IPython.display import HTML, display
from mgrs import MGRS
from rasterio.transform import rowcol
from shapely.geometry import Point
from torchgeo.models import RCF

CDL_CODE_TO_NAME = {
    0: "Background",
    1: "Corn",
    2: "Cotton",
    3: "Rice",
    4: "Sorghum",
    5: "Soybeans",
    6: "Sunflower",
    10: "Peanuts",
    11: "Tobacco",
    12: "Sweet Corn",
    13: "Pop or Orn Corn",
    14: "Mint",
    21: "Barley",
    22: "Durum Wheat",
    23: "Spring Wheat",
    24: "Winter Wheat",
    25: "Other Small Grains",
    26: "Dbl Crop WinWht/Soybeans",
    27: "Rye",
    28: "Oats",
    29: "Millet",
    30: "Speltz",
    31: "Canola",
    32: "Flaxseed",
    33: "Safflower",
    34: "Rape Seed",
    35: "Mustard",
    36: "Alfalfa",
    37: "Other Hay/Non Alfalfa",
    38: "Camelina",
    39: "Buckwheat",
    41: "Sugarbeets",
    42: "Dry Beans",
    43: "Potatoes",
    44: "Other Crops",
    45: "Sugarcane",
    46: "Sweet Potatoes",
    47: "Misc Vegs & Fruits",
    48: "Watermelons",
    49: "Onions",
    50: "Cucumbers",
    51: "Chick Peas",
    52: "Lentils",
    53: "Peas",
    54: "Tomatoes",
    55: "Caneberries",
    56: "Hops",
    57: "Herbs",
    58: "Clover/Wildflowers",
    59: "Sod/Grass Seed",
    60: "Switchgrass",
    61: "Fallow/Idle Cropland",
    63: "Forest",
    64: "Shrubland",
    65: "Barren",
    66: "Cherries",
    67: "Peaches",
    68: "Apples",
    69: "Grapes",
    70: "Christmas Trees",
    71: "Other Tree Crops",
    72: "Citrus",
    74: "Pecans",
    75: "Almonds",
    76: "Walnuts",
    77: "Pears",
    81: "Clouds/No Data",
    82: "Developed",
    83: "Water",
    87: "Wetlands",
    88: "Nonag/Undefined",
    92: "Aquaculture",
    111: "Open Water",
    112: "Perennial Ice/Snow",
    121: "Developed/Open Space",
    122: "Developed/Low Intensity",
    123: "Developed/Med Intensity",
    124: "Developed/High Intensity",
    131: "Barren",
    141: "Deciduous Forest",
    142: "Evergreen Forest",
    143: "Mixed Forest",
    152: "Shrubland",
    176: "Grass/Pasture",
    190: "Woody Wetlands",
    195: "Herbaceous Wetlands",
    204: "Pistachios",
    205: "Triticale",
    206: "Carrots",
    207: "Asparagus",
    208: "Garlic",
    209: "Cantaloupes",
    210: "Prunes",
    211: "Olives",
    212: "Oranges",
    213: "Honeydew Melons",
    214: "Broccoli",
    215: "Avocados",
    216: "Peppers",
    217: "Pomegranates",
    218: "Nectarines",
    219: "Greens",
    220: "Plums",
    221: "Strawberries",
    222: "Squash",
    223: "Apricots",
    224: "Vetch",
    225: "Dbl Crop WinWht/Corn",
    226: "Dbl Crop Oats/Corn",
    227: "Lettuce",
    228: "Dbl Crop Triticale/Corn",
    229: "Pumpkins",
    230: "Dbl Crop Lettuce/Durum Wht",
    231: "Dbl Crop Lettuce/Cantaloupe",
    232: "Dbl Crop Lettuce/Cotton",
    233: "Dbl Crop Lettuce/Barley",
    234: "Dbl Crop Durum Wht/Sorghum",
    235: "Dbl Crop Barley/Sorghum",
    236: "Dbl Crop WinWht/Sorghum",
    237: "Dbl Crop Barley/Corn",
    238: "Dbl Crop WinWht/Cotton",
    239: "Dbl Crop Soybeans/Cotton",
    240: "Dbl Crop Soybeans/Oats",
    241: "Dbl Crop Corn/Soybeans",
    242: "Blueberries",
    243: "Cabbage",
    244: "Cauliflower",
    245: "Celery",
    246: "Radishes",
    247: "Turnips",
    248: "Eggplants",
    249: "Gourds",
    250: "Cranberries",
    254: "Dbl Crop Barley/Soybeans",
}


"""Download crop calendar files into ./data if they don't exist."""
crop_calendar_files = {
    "summer": {"start": "sc_sos_3x3_v2.tiff", "end": "sc_eos_3x3_v2.tiff"},
    "winter": {"start": "wc_sos_3x3_v2.tiff", "end": "wc_eos_3x3_v2.tiff"},
}


def granule_codes_from_bbox(lat_min, lat_max, lon_min, lon_max):
    # Handle antimeridian by splitting if needed
    if lon_min <= lon_max:
        lon_ranges = [(lon_min, lon_max)]
    else:
        lon_ranges = [(lon_min, 180.0), (-180.0, lon_max)]

    granules = set()
    for lomin, lomax in lon_ranges:
        lat_start = int(math.ceil(lat_min / 10.0) * 10)
        lat_end = int(math.ceil(lat_max / 10.0) * 10)
        lon_start = int(math.floor(lomin / 10.0) * 10)
        lon_end = int(math.floor(lomax / 10.0) * 10)

        for lat_tl in range(lat_start, lat_end + 1, 10):
            for lon_tl in range(lon_start, lon_end + 1, 10):
                lat_hemi = "N" if lat_tl >= 0 else "S"
                lon_hemi = "E" if lon_tl >= 0 else "W"
                lat_str = f"{abs(lat_tl):02d}{lat_hemi}"
                lon_str = f"{abs(lon_tl):03d}{lon_hemi}"
                granules.add((lat_str, lon_str))
    return sorted(granules)


def download_glad_granule(filename, layer="lossyear", version="GFC-2024-v1.12"):
    base_url = f"https://storage.googleapis.com/earthenginepartners-hansen/{version}/"
    try:
        url = base_url + filename
        urllib.request.urlretrieve(url, "data/" + filename)
    except Exception as e:
        print(f"Failed to download {url}: {str(e)}")
        return False


def hansen_filenames_from_bbox(
    lat_min, lat_max, lon_min, lon_max, layer="lossyear", version="GFC-2024-v1.12"
):
    out = []
    for lat_str, lon_str in granule_codes_from_bbox(lat_min, lat_max, lon_min, lon_max):
        fname = f"Hansen_{version}_{layer}_{lat_str}_{lon_str}.tif"
        out.append(fname)
    return out


def calculate_window_dates(sos_date, eos_date):
    """
    Calculate window dates based on SOS and EOS dates.
    """

    sos = datetime.strptime(sos_date, "%Y-%m-%d")
    eos = datetime.strptime(eos_date, "%Y-%m-%d")

    win_a_start = (sos - timedelta(days=15)).strftime("%Y-%m-%d")
    win_a_end = (sos + timedelta(days=15)).strftime("%Y-%m-%d")
    win_b_start = (eos - timedelta(days=30)).strftime("%Y-%m-%d")
    win_b_end = eos.strftime("%Y-%m-%d")

    return win_a_start, win_a_end, win_b_start, win_b_end


def get_date_from_day_of_year(day_of_year: int, year: int) -> str:
    if day_of_year < 1 or day_of_year > 366:
        raise ValueError("day_of_year must be between 1 and 366")
    base_date = datetime(year, 1, 1)
    result_date = base_date + timedelta(days=day_of_year - 1)
    if day_of_year == 366 and result_date.year != year:
        raise ValueError(f"{year} is not a leap year.")
    return result_date.strftime("%Y-%m-%d")


def get_dates_from_tifs(
    point: Point,
    start_season_tif_path: str,
    end_season_tif_path: str,
    year=2020,
    season_type="winter",
):
    """
    Extract start and end crop calendar dates (day-of-year and date) from GeoTIFFs using rasterio.

    Args:
        point: shapely.geometry.Point
        start_season_tif_path: path to the start season GeoTIFF
        end_season_tif_path: path to the end season GeoTIFF
        year: crop calendar reference year

    Returns:
        (start_day, end_day, start_date_str, end_date_str)
    """
    with rasterio.open(start_season_tif_path) as start_src:
        row, col = rowcol(start_src.transform, point.x, point.y)
        start_day = start_src.read(1)[row, col]

    with rasterio.open(end_season_tif_path) as end_src:
        row, col = rowcol(end_src.transform, point.x, point.y)
        end_day = end_src.read(1)[row, col]

    # Handle crop calendars that span across years, like a season starting in September and ending in March
    end_year = year + 1 if end_day < start_day else year

    start_date = get_date_from_day_of_year(int(start_day), year)
    end_date = get_date_from_day_of_year(int(end_day), end_year)

    return start_date, end_date


def download_crop_calendars(crop_calendar_dir="./"):
    os.makedirs(crop_calendar_dir, exist_ok=True)
    base_url = "https://github.com/fieldsoftheworld/ftw-qgis-plugin/raw/main/resources/global_crop_calendars/"

    for season, files in crop_calendar_files.items():
        for file_type, filename in files.items():
            local_path = os.path.join(crop_calendar_dir, filename)
            if not os.path.exists(local_path):
                try:
                    urllib.request.urlretrieve(base_url + filename, local_path)
                except Exception as e:
                    print(f"Failed to download {filename}: {str(e)}")
                    return False
    return True


def get_best_images(
    win_a_start, win_a_end, win_b_start, win_b_end, s2_tile_id, max_cloud_cover=20
):
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )

    def find_best_image(start_date, end_date, cloud_threshold, s2_tile_id):
        time_range = f"{start_date}/{end_date}"
        print(
            f"Searching for images between {start_date} and {end_date} with cloud cover < {cloud_threshold}%"
        )

        search = catalog.search(
            collections=["sentinel-2-l2a"],
            datetime=time_range,
            query={
                "eo:cloud_cover": {"lt": cloud_threshold},
                "s2:mgrs_tile": {"eq": s2_tile_id},
                "s2:nodata_pixel_percentage": {"lt": 10},
            },
        )

        items = search.item_collection()
        if len(items) == 0:
            print(f"No images found with cloud cover < {cloud_threshold}%")
            return None

        best_item = min(
            items, key=lambda item: item.properties.get("eo:cloud_cover", 100)
        )
        cloud_cover = best_item.properties.get("eo:cloud_cover", 100)
        print(
            f"Found image from {best_item.datetime.date()} with {cloud_cover}% cloud coverage"
        )
        return best_item

    cloud_thresholds = [max_cloud_cover, 50, 70, 100]
    win_a = None
    win_b = None

    for threshold in cloud_thresholds:
        if win_a is None:
            win_a = find_best_image(win_a_start, win_a_end, threshold, s2_tile_id)
        if win_b is None:
            win_b = find_best_image(win_b_start, win_b_end, threshold, s2_tile_id)
        if win_a is not None and win_b is not None:
            break

    if win_a is None:
        raise ValueError(
            f"Could not find suitable images for window A ({win_a_start} to {win_a_end}) even with 100% cloud cover"
        )
    if win_b is None:
        raise ValueError(
            f"Could not find suitable images for window B ({win_b_start} to {win_b_end}) even with 100% cloud cover"
        )

    return win_a, win_b


def show_previews(a, b):
    href_a = a.assets["rendered_preview"].href
    href_b = b.assets["rendered_preview"].href

    return display(
        HTML(f"""
        <div style="display: flex; gap: 5%">
            <div width="50%">
                <h4>Window A</h4>
                <img src="{href_a}" style="max-width: 100%; max-height: 50vh" />
            </div>
            <div width="50%">
                <h4>Window B</h4>
                <img src="{href_b}" style="max-width: 100%; max-height: 50vh" />
            </div>
        </div>
    """)
    )


### MGRS Tile Selector

selected_grid_layer = None
selected_tile_id = None  # Module-level variable to store selected tile


def get_tile_id(ft):
    return ft.get("properties", {}).get("Name")


def pick_mgrs_tile(tile_id):
    with open("s2-grid.json") as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    feature_map = {}
    for ft in features:
        tid = get_tile_id(ft)
        feature_map[tid] = ft

    m = leafmap.Map(center=(0, 0), zoom=1, draw_control=False, measure_control=False)

    # Base layer: the whole grid (light style, hover emphasis)
    grid_layer = GeoJSON(
        data=geojson,
        style={"color": "#666666", "weight": 0.25, "fillOpacity": 0.05},
        hover_style={"weight": 2, "fillOpacity": 0.10},
        name="MGRS Tiles",
    )
    m.add_layer(grid_layer)

    status = widgets.HTML("<b>Click a tile to select its MGRS ID.</b>")
    display(status)
    display(m)

    def highlight_tile(fid):
        global selected_grid_layer
        """Replace the highlight layer with the selected feature."""
        # Remove old highlight
        if selected_grid_layer is not None:
            try:
                m.remove_layer(selected_grid_layer)
            except Exception:
                pass
            selected_grid_layer = None

        if fid not in feature_map:
            return

        # Create a single-feature GeoJSON for the highlight
        selected_grid_layer = GeoJSON(
            data=feature_map[fid],
            style={"color": "#ff0000", "weight": 3, "fillOpacity": 0.15},
            name="Selected Tile",
        )
        m.add_layer(selected_grid_layer)

    def select_tile(fid):
        global selected_tile_id
        selected_tile_id = fid
        highlight_tile(fid)
        status.value = f"<b>Selected tile:</b> <code>{fid}</code>"

    # ----------------------------
    # Feature click handler
    # ----------------------------
    def on_grid_click(**kwargs):
        # ipyleaflet passes a dict with 'feature' and 'coordinates'
        ft = kwargs.get("feature") or {}
        fid = get_tile_id(ft)
        select_tile(fid)

    grid_layer.on_click(on_grid_click)

    if tile_id:
        select_tile(tile_id)


def get_selected_tile_id():
    """Helper function to get the currently selected tile ID"""
    return selected_tile_id


class RCFWithCustomMaskPooling(RCF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def forward_masked(self, x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """WARNING: This method doesn't work on batches of images, only on single images."""

        assert x.dim() == 3, "Input tensor must have 3 dimensions (C, H, W)"
        x1a = F.relu(
            F.conv2d(x, self.weights, bias=self.biases, stride=1, padding=0),
            inplace=True,
        )
        x1b = F.relu(
            -F.conv2d(x, self.weights, bias=self.biases, stride=1, padding=0),
            inplace=False,
        )
        padding = self.weights.shape[-1] // 2
        mask = mask[padding:-padding, padding:-padding]

        x1a = torch.mean(x1a[:, mask], dim=1, keepdim=False)
        x1b = torch.mean(x1b[:, mask], dim=1, keepdim=False)
        output = torch.cat((x1a, x1b), dim=0)
        return output


def download_and_run(tile_id: str, season: str, year: int, buffer: float = 0.1):
    """Download the data for a given tile and run the FTW model to generate boundaries.

    Args:
        tile_id (str): The MGRS tile ID (e.g., '21LXF').
        season (str): The growing season ('winter' or 'summer').
        year (int): The year of interest (e.g., 2022).
        buffer (float): ROI half-width in degrees around the center (0.1 -> 0.2 deg).

    Returns:
        str: The filename of the generated boundaries file.
    """
    image_filename = f"ftw_input_{tile_id}_{season}_{year}.tif"
    output_filename = f"ftw_predictions_{tile_id}_{season}_{year}.tif"
    filtered_output_filename = f"ftw_predictions_filtered_{tile_id}_{season}_{year}.tif"
    boundaries_filename = f"ftw_boundaries_{tile_id}_{season}_{year}.gpkg"

    lat, lon = MGRS().toLatLon(
        tile_id + "5000050000"
    )  # This gets the center of the MGRS tile
    tile_center = Point(lon, lat)

    bbox_string = f"{lon - buffer},{lat - buffer},{lon + buffer},{lat + buffer}"

    if os.path.exists(boundaries_filename):
        print(f"Boundaries file {boundaries_filename} already exists. Skipping.")
        return {
            "image_filename": image_filename,
            "output_filename": output_filename,
            "filtered_output_filename": filtered_output_filename,
            "boundaries_filename": boundaries_filename,
            "bbox_string": bbox_string,
        }

    start_tif = crop_calendar_files[season]["start"]
    end_tif = crop_calendar_files[season]["end"]

    start_date, end_date = get_dates_from_tifs(
        point=tile_center,
        start_season_tif_path=start_tif,
        end_season_tif_path=end_tif,
        year=year,
        season_type=season,
    )

    win_a_start, win_a_end, win_b_start, win_b_end = calculate_window_dates(
        start_date, end_date
    )
    win_a, win_b = get_best_images(
        win_a_start, win_a_end, win_b_start, win_b_end, s2_tile_id=tile_id
    )

    subprocess.run(
        [
            "ftw",
            "inference",
            "download",
            "--win_a",
            win_a.id,
            "--win_b",
            win_b.id,
            "--out",
            image_filename,
            "--overwrite",
            "--bbox",
            bbox_string,
        ],
        check=True,
    )

    subprocess.run(
        [
            "ftw",
            "model",
            "download",
            "--type",
            "THREE_CLASS_FULL",
            "-o",
            "3_Class_FULL_FTW_Pretrained.ckpt",
        ],
        check=True,
    )

    model_filename = "3_Class_FULL_FTW_Pretrained.ckpt"

    if torch.backends.mps.is_available():
        print("Running inference with MPS mode enabled")
        subprocess.run(
            [
                "ftw",
                "inference",
                "run",
                image_filename,
                "--out",
                output_filename,
                "--gpu",
                "0",
                "--mps_mode",
                "--model",
                model_filename,
                "--overwrite",
            ],
            check=True,
        )
    elif torch.cuda.is_available():
        print("Running inference with GPU enabled")
        subprocess.run(
            [
                "ftw",
                "inference",
                "run",
                image_filename,
                "--out",
                output_filename,
                "--gpu",
                "0",
                "--model",
                model_filename,
                "--overwrite",
            ],
            check=True,
        )
    else:
        print("Running inference with CPU only mode")
        subprocess.run(
            [
                "ftw",
                "inference",
                "run",
                image_filename,
                "--out",
                output_filename,
                "--model",
                model_filename,
                "--overwrite",
            ],
            check=True,
        )

    subprocess.run(
        [
            "ftw",
            "inference",
            "filter-by-lulc",
            output_filename,
            "--out",
            filtered_output_filename,
            "--overwrite",
        ],
        check=True,
    )

    subprocess.run(
        [
            "ftw",
            "inference",
            "polygonize",
            filtered_output_filename,
            "--out",
            boundaries_filename,
            "-f",
        ],
        check=True,
    )

    return {
        "image_filename": image_filename,
        "output_filename": output_filename,
        "filtered_output_filename": filtered_output_filename,
        "boundaries_filename": boundaries_filename,
        "bbox_string": bbox_string,
    }


## <- [GOAL] Fast-mode CDL source: a tiny committed clip vs. the >10 GB CONUS download.
# REVIEW REQUIRED  (data integrity: picks which CDL raster feeds the crop labels)
def ensure_cdl_sample(
    sample_path: str = "samples/cdl_14TPN_2023.tif",
    full_path: str = "data/cdl/2023_30m_cdls.tif",
    boundaries_path: str = "ftw_boundaries_14TPN_summer_2023.gpkg",
) -> str:
    """Return a CDL raster path covering the crop-type ROI without the CONUS download.

    Uses the committed ~0.5 MB clip in ``samples/`` (built by ``make_cdl_sample.py``).
    If the field boundaries fall outside the clip (e.g. someone changed the tile), warns
    and falls back to the full CDL, downloading it via TorchGeo if absent.

    Args:
        sample_path (str): committed CDL clip over the default 14TPN ROI.
        full_path (str): full CONUS CDL raster (used only on fallback).
        boundaries_path (str): field boundaries used to verify the clip covers the ROI.

    Returns:
        str: path to a CDL raster suitable for the zonal-majority join.
    """
    import geopandas as gpd

    if os.path.exists(sample_path):
        with rasterio.open(sample_path) as src:
            b = src.bounds
            try:
                fb = gpd.read_file(boundaries_path).to_crs(src.crs).total_bounds
                covered = (
                    b.left <= fb[0] and b.bottom <= fb[1]
                    and b.right >= fb[2] and b.top >= fb[3]
                )
            except Exception:
                covered = True  # cannot verify (no boundaries yet) -> trust the clip
        if covered:
            return sample_path
        print("⚠️  Fields fall outside the CDL sample clip; using the full CDL instead.")

    if not os.path.exists(full_path):
        from torchgeo.datasets import CDL

        CDL(paths="data/cdl", years=[2023], download=True)
    return full_path
