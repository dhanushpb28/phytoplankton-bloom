import copernicusmarine
import tempfile
import os

def fetch_daily_data(date, lat_min, lat_max, lon_min, lon_max):
    """
    Download Copernicus data for ONE day into a date-isolated temp folder.
    This avoids Copernicus caching / overwrite issues.
    """

    # Create unique folder per day
    day_dir = os.path.join(tempfile.gettempdir(), f"cmems_{date}")
    os.makedirs(day_dir, exist_ok=True)

    files = {
        "pft": os.path.join(day_dir, f"pft_{date}.nc"),
        "bio": os.path.join(day_dir, f"bio_{date}.nc"),
        "nut": os.path.join(day_dir, f"nut_{date}.nc"),
        "cur": os.path.join(day_dir, f"cur_{date}.nc"),
        "sst": os.path.join(day_dir, f"sst_{date}.nc"),
    }

    # -------------------------------------------------
    # 1. Phytoplankton (chl, phyc)
    # -------------------------------------------------
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
        output_directory=day_dir,
        output_filename=f"pft_{date}.nc"
    )

    # -------------------------------------------------
    # 2. Net Primary Production
    # -------------------------------------------------
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
        output_directory=day_dir,
        output_filename=f"bio_{date}.nc"
    )

    # -------------------------------------------------
    # 3. Nutrients
    # -------------------------------------------------
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
        output_directory=day_dir,
        output_filename=f"nut_{date}.nc"
    )

    # -------------------------------------------------
    # 4. Currents
    # -------------------------------------------------
    copernicusmarine.subset(
        dataset_id="cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
        variables=["uo", "vo"],
        minimum_latitude=lat_min,
        maximum_latitude=lat_max,
        minimum_longitude=lon_min,
        maximum_longitude=lon_max,
        start_datetime=date,
        end_datetime=date,
        minimum_depth=0,
        maximum_depth=1,
        output_directory=day_dir,
        output_filename=f"cur_{date}.nc"
    )

    # -------------------------------------------------
    # 5. SST anomaly
    # -------------------------------------------------
    copernicusmarine.subset(
        dataset_id="cmems_mod_glo_phy_anfc_0.083deg-sst-anomaly_P1D-m",
        variables=["sea_surface_temperature_anomaly"],
        minimum_latitude=lat_min,
        maximum_latitude=lat_max,
        minimum_longitude=lon_min,
        maximum_longitude=lon_max,
        start_datetime=date,
        end_datetime=date,
        output_directory=day_dir,
        output_filename=f"sst_{date}.nc"
    )

    return files
