import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np

def plot_chl_bloom(ds, bloom_mask):
    fig = plt.figure(figsize=(6,6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.pcolormesh(ds.longitude, ds.latitude, np.log1p(ds.chl), cmap="viridis")
    ax.contour(ds.longitude, ds.latitude, bloom_mask, colors="red", linewidths=0.5)
    ax.coastlines()
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    return fig
