import boto3
import xarray as xr
import numpy as np
import tempfile
import os
import datetime

# =========================================================
# CONFIG
# =========================================================
BUCKET = "hab-bloom-db-2026"
PREFIX = "daily/"

s3 = boto3.client("s3")


def _download_from_s3(s3_key, local_path):
    s3.download_file(BUCKET, s3_key, local_path)


# =========================================================
# MAIN LOADER
# =========================================================
def load_from_s3(
    start_date,
    end_date,
    lat_min,
    lat_max,
    lon_min,
    lon_max
):
    """
    Load Copernicus NetCDF data from S3 and return ONE clean Dataset.

    Final dataset:
        dims: time, latitude, longitude
        vars: chl, nppv, no3, po4, sst, uo, vo
    """

    tmp_dir = tempfile.gettempdir()
    daily_datasets = []
    current = start_date

    while current <= end_date:

        y = current.strftime("%Y")
        m = current.strftime("%m")
        d = current.strftime("%d")
        base = f"{PREFIX}{y}/{m}/{d}/"

        files = {
            "pft.nc": ["chl", "phyc"],   # ⭐ load TWO vars from same file
            "nut.nc": ["no3", "po4"],
            "bio.nc": ["nppv"],
            "sst.nc": ["sea_surface_temperature_anomaly"],
            "cur.nc": ["uo", "vo"],
        }


        data_vars = {}
        master_lat = None
        master_lon = None

        # -----------------------------------------------------
        # Download and process each variable
        # -----------------------------------------------------
        for fname, variables in files.items():

            key = base + fname
            local = os.path.join(tmp_dir, f"{fname}_{y}{m}{d}.nc")

            try:
                _download_from_s3(key, local)
                ds = xr.open_dataset(local)

                # Remove depth
                if "depth" in ds.dims:
                    ds = ds.isel(depth=0, drop=True)
                if "depth" in ds.coords:
                    ds = ds.drop_vars("depth")

                # Remove time (we control time dimension)
                if "time" in ds.dims:
                    ds = ds.isel(time=0, drop=True)
                if "time" in ds.coords:
                    ds = ds.drop_vars("time")

                # Use chlorophyll grid as MASTER grid
                if "chl" in ds:
                    master_lat = ds.latitude
                    master_lon = ds.longitude

                # Regrid other datasets to chl grid
                if master_lat is not None and "chl" not in ds:
                    ds = ds.interp(
                        latitude=master_lat,
                        longitude=master_lon,
                        method="nearest"
                    )

                # Extract requested variables
                for var in variables:
                    if var in ds:
                        data_vars[var] = ds[var]

            except Exception as e:
                print(f"⚠️ Missing {fname} for {current}: {e}")
                continue

        if not data_vars:
            current += datetime.timedelta(days=1)
            continue

        # -----------------------------------------------------
        # Merge variables safely (same grid now)
        # -----------------------------------------------------
        ds_day = xr.merge(list(data_vars.values()), join="exact")

        # -----------------------------------------------------
        # Add daily time dimension
        # -----------------------------------------------------
        ds_day = ds_day.expand_dims(time=[np.datetime64(current)])

        daily_datasets.append(ds_day)
        current += datetime.timedelta(days=1)

    if not daily_datasets:
        raise RuntimeError("❌ No data loaded from S3")

    # ---------------------------------------------------------
    # Concatenate all days
    # ---------------------------------------------------------
    ds_all = xr.concat(daily_datasets, dim="time")

    # ---------------------------------------------------------
    # Spatial subset
    # ---------------------------------------------------------
    ds_all = ds_all.sel(
        latitude=slice(lat_min, lat_max),
        longitude=slice(lon_min, lon_max)
    )

    return ds_all
