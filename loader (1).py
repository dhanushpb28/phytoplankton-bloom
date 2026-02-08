import copernicusmarine
import xarray as xr
import tempfile
import os
import numpy as np

def fetch_and_load(
    date,
    lat_min, lat_max,
    lon_min, lon_max
):
    """
    Lightweight Copernicus fetch (ERDDAP-style)
    Fetches ONLY what is needed, ONLY when called
    """

    tmp_dir = tempfile.gettempdir()

    pft_file = os.path.join(tmp_dir, "pft.nc")
    bio_file = os.path.join(tmp_dir, "bio.nc")
    nut_file = os.path.join(tmp_dir, "nut.nc")

    # ---------- CHL + PHYTOPLANKTON CARBON ----------
    copernicusmarine.subset(
        dataset_id="cmems_mod_glo_bgc-pft_anfc_0.25deg_P1D-m",
        variables=["chl", "phyc"],
        minimum_latitude=lat_min,
        maximum_latitude=lat_max,
        minimum_longitude=lon_min,
        maximum_longitude=lon_max,
        start_datetime=date,
        end_datetime=date,
        minimum_depth=0,
        maximum_depth=1,
        output_directory=tmp_dir,
        output_filename="pft.nc"
    )

    # ---------- NET PRIMARY PRODUCTION ----------
    copernicusmarine.subset(
        dataset_id="cmems_mod_glo_bgc-bio_anfc_0.25deg_P1D-m",
        variables=["nppv"],
        minimum_latitude=lat_min,
        maximum_latitude=lat_max,
        minimum_longitude=lon_min,
        maximum_longitude=lon_max,
        start_datetime=date,
        end_datetime=date,
        minimum_depth=0,
        maximum_depth=1,
        output_directory=tmp_dir,
        output_filename="bio.nc"
    )

    # ---------- NUTRIENTS ----------
    copernicusmarine.subset(
        dataset_id="cmems_mod_glo_bgc-nut_anfc_0.25deg_P1D-m",
        variables=["no3", "po4"],
        minimum_latitude=lat_min,
        maximum_latitude=lat_max,
        minimum_longitude=lon_min,
        maximum_longitude=lon_max,
        start_datetime=date,
        end_datetime=date,
        minimum_depth=0,
        maximum_depth=1,
        output_directory=tmp_dir,
        output_filename="nut.nc"
    )

    # ---------- LOAD ----------
    pft = xr.open_dataset(pft_file, engine="h5netcdf")
    bio = xr.open_dataset(bio_file, engine="h5netcdf")
    nut = xr.open_dataset(nut_file, engine="h5netcdf")

    ds = xr.merge([pft, bio, nut])

    # surface + date
    ds = ds.isel(depth=ds.depth.argmin())
    ds = ds.sel(time=np.datetime64(date))

    return ds
