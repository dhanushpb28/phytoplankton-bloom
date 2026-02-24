from src.data.s3_loader import load_from_s3
import datetime
import numpy as np

# choose two days to compare
day1 = datetime.date(2026,2,1)
day2 = datetime.date(2026,2,2)

ds = load_from_s3(
    start_date=day1,
    end_date=day2,
    lat_min=-50,
    lat_max=-10,
    lon_min=100,
    lon_max=170
)

print(ds)
ds1 = ds.sel(time=str(day1))
ds2 = ds.sel(time=str(day2))

print("\n==============================")
print("DAY 1:", day1)
print("==============================")
print(ds1)

print("\n==============================")
print("DAY 2:", day2)
print("==============================")
print(ds2)
variables = ["chl","phyc","no3","po4","nppv",
             "sea_surface_temperature_anomaly","uo","vo"]

print("\n\n========== STATISTICS COMPARISON ==========\n")

for var in variables:
    v1 = ds1[var].values
    v2 = ds2[var].values

    print(f"\n🔹 {var.upper()}")
    print("Day1 min/max:", np.nanmin(v1), np.nanmax(v1))
    print("Day2 min/max:", np.nanmin(v2), np.nanmax(v2))
    print("Difference mean:", np.nanmean(v2 - v1))

LAT_MIN, LAT_MAX = -45, -10
LON_MIN, LON_MAX = 110, 155

ds1 = ds1.sel(latitude=slice(LAT_MIN, LAT_MAX),
              longitude=slice(LON_MIN, LON_MAX))

ds2 = ds2.sel(latitude=slice(LAT_MIN, LAT_MAX),
              longitude=slice(LON_MIN, LON_MAX))

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def plot_compare(var):
    fig, axs = plt.subplots(
        1,2, figsize=(12,5),
        subplot_kw={"projection": ccrs.PlateCarree()}
    )

    for ax, data, title in zip(
        axs,
        [ds1[var], ds2[var]],
        [str(day1), str(day2)]
    ):
        ax.set_extent([110,155,-45,-10])

        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.LAND, facecolor="lightgray")

        d = np.log1p(data) if var=="chl" else data

        mesh = ax.pcolormesh(
            ds.longitude, ds.latitude, d,
            cmap="viridis", shading="auto",
            transform=ccrs.PlateCarree()
        )

        ax.set_title(f"{var} — {title}")

    plt.colorbar(mesh, ax=axs, shrink=0.6)
    plt.show()


# compare chlorophyll visually
plot_compare("chl")
