import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
import tempfile, os

# =========================================================
# 1️⃣ Chlorophyll + Bloom Overlay
# =========================================================
def plot_chl_bloom(ds, bloom_mask, lat_min, lat_max, lon_min, lon_max):
    fig = plt.figure(figsize=(6,6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([lon_min, lon_max, lat_min, lat_max])

    pcm = ax.pcolormesh(ds.longitude, ds.latitude, np.log1p(ds.chl),
                        cmap="viridis", shading="auto", transform=ccrs.PlateCarree())

    ax.contour(ds.longitude, ds.latitude, bloom_mask,
               levels=[0.5], colors="red", linewidths=0.8,
               transform=ccrs.PlateCarree())

    ax.coastlines(resolution="10m")
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    plt.colorbar(pcm, ax=ax, shrink=0.75, label="log(1+Chl)")
    ax.set_title("Chlorophyll Bloom Detection")
    return fig

# =========================================================
# 2. Bloom Intensity Classification Map
# =========================================================
# ===================================================
# Mean Bloom Map (replaces intensity classification)
# ===================================================

# =========================================================
# 2️⃣ Mean Bloom Map
# =========================================================
def plot_mean_bloom_map(ds, threshold, lat_min, lat_max, lon_min, lon_max):
    chl_mean = ds.chl.mean(dim="time")
    bloom = chl_mean.where(chl_mean > threshold)
    vmax = np.nanpercentile(bloom,95)

    fig = plt.figure(figsize=(8,5))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([lon_min, lon_max, lat_min, lat_max])

    bloom.plot(ax=ax, cmap="Reds", vmin=threshold, vmax=vmax,
               cbar_kwargs={"label":"Mean Chlorophyll"})
    ax.coastlines()
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.set_title(f"Mean Bloom (> {threshold} mg/m³)")
    return fig
    


# =========================================================
# 3. Generic Variable Map (NO3, PO4, NPP, SST, Currents)
# =========================================================
def plot_variable_map(ds, var, title, lat_min, lat_max, lon_min, lon_max):
    fig = plt.figure(figsize=(6,6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([lon_min, lon_max, lat_min, lat_max])

    data = np.log1p(ds[var]) if var=="chl" else ds[var]
    pcm = ax.pcolormesh(ds.longitude, ds.latitude, data,
                        cmap="viridis", shading="auto",
                        transform=ccrs.PlateCarree())

    ax.coastlines()
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    plt.colorbar(pcm, ax=ax, shrink=0.75)
    ax.set_title(title)
    return fig


# =========================================================

# =========================================================
# 4️⃣ Animation
# =========================================================
def animate_variable(ds, var, lat_min, lat_max, lon_min, lon_max):
    gif = os.path.join(tempfile.gettempdir(), f"{var}.gif")
    times = ds.time.values

    fig, ax = plt.subplots(figsize=(10,6), subplot_kw={"projection":ccrs.PlateCarree()})

    def update(frame):
        ax.clear()
        ax.set_extent([lon_min, lon_max, lat_min, lat_max])
        ax.add_feature(cfeature.COASTLINE)
        data = np.log1p(ds[var].isel(time=frame)) if var=="chl" else ds[var].isel(time=frame)
        img = data.plot(ax=ax, transform=ccrs.PlateCarree(), add_colorbar=False)
        ax.set_title(f"{var.upper()} {str(times[frame])[:10]}")
        return img

    anim = FuncAnimation(fig, update, frames=len(times))
    anim.save(gif, writer=PillowWriter(fps=2))
    plt.close()
    return gif

# =========================================================
# 5. Statistics Charts
# =========================================================
# =========================================================
# Research-grade Bloom Composition Chart
# =========================================================
def plot_pie_coverage(bloom_mask, ds):
    """
    Research-style bloom composition:
    Shows % ocean area under bloom intensity classes.
    """

    chl = ds.chl.values.flatten()

    # remove NaNs (land pixels etc.)
    chl = chl[~np.isnan(chl)]

    # Scientific bloom classes
    non_bloom = np.sum(chl < 2)
    moderate  = np.sum((chl >= 2) & (chl < 5))
    high      = np.sum(chl >= 5)

    total = non_bloom + moderate + high

    labels = [
        "Non-bloom (<2)",
        "Moderate Bloom (2–5)",
        "High Bloom (>5)"
    ]

    values = np.array([non_bloom, moderate, high]) / total * 100

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(6,6))

    wedges, texts, autotexts = ax.pie(
        values,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.8,
        wedgeprops=dict(edgecolor="white"),
        textprops=dict(fontsize=10)
    )

    # donut style for research look
    centre_circle = plt.Circle((0,0),0.55,fc='white')
    fig.gca().add_artist(centre_circle)

    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1,0.5))
    ax.set_title("Ocean Area Under Bloom Conditions")

    return fig

def plot_bloom_timeseries(ds, bloom_mask):
    """
    % ocean area under bloom vs time
    """
    coverage = bloom_mask.mean(dim=["latitude","longitude"]) * 100

    fig, ax = plt.subplots(figsize=(7,4))
    ax.plot(ds.time.values, coverage, marker="o", linewidth=2)

    ax.set_title("Bloom Coverage Time Series")
    ax.set_ylabel("Bloom Area (%)")
    ax.set_xlabel("Date")
    ax.grid(True)

    return fig
def plot_environment_correlation(ds):
    """
    Correlation between bloom intensity and environmental drivers
    """
    # spatial mean time series
    df = ds.mean(dim=["latitude","longitude"]).to_dataframe()

    vars_keep = [
        "chl","phyc","nppv","no3","po4",
        "sea_surface_temperature_anomaly","uo","vo"
    ]

    df = df[vars_keep].dropna()

    corr = df.corr()

    fig, ax = plt.subplots(figsize=(6,5))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)

    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.columns)

    plt.colorbar(im, ax=ax, label="Correlation")
    ax.set_title("Environmental Drivers Correlation Matrix")

    return fig

def plot_bloom_risk_radar(ds):
    """
    Multi-factor bloom risk indicator
    """
    means = ds.mean(dim=["time","latitude","longitude"])

    features = {
        "Chl": float(means.chl),
        "NPP": float(means.nppv),
        "NO3": float(means.no3),
        "PO4": float(means.po4),
        "SST Anom": float(abs(means.sea_surface_temperature_anomaly)),
        "Currents": float(np.sqrt(means.uo**2 + means.vo**2)),
    }

    labels = list(features.keys())
    values = list(features.values())
    values += values[:1]

    angles = np.linspace(0, 2*np.pi, len(labels)+1)

    fig = plt.figure(figsize=(5,5))
    ax = plt.subplot(111, polar=True)

    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_title("Bloom Risk Indicator")

    return fig


def plot_bar_intensity(ds):
    chl = ds.chl.values.flatten()

    low = np.sum(chl < 2)
    mid = np.sum((chl >= 2) & (chl < 5))
    high = np.sum(chl >= 5)

    fig, ax = plt.subplots()
    ax.bar(["Low", "Moderate", "High"], [low, mid, high], color="orange")
    ax.set_title("Bloom Intensity Distribution")
    ax.set_ylabel("Grid Cells")

    return fig

def plot_forecast_map(lat, lon, data, title):

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib.pyplot as plt
    import numpy as np
    from shapely.geometry import Point
    from shapely.ops import unary_union
    import cartopy.io.shapereader as shpreader

    # Physical constraint
    data = np.clip(data, 0, None)

    # Log transform (same as detection)
    log_data = np.log1p(data)

    # -------------------------------------------------
    # 🔥 LAND MASK (THIS IS THE IMPORTANT PART)
    # -------------------------------------------------

    # Get Natural Earth land polygons
    land_shp = shpreader.natural_earth(
        resolution='10m',
        category='physical',
        name='land'
    )
    land_geoms = list(shpreader.Reader(land_shp).geometries())
    land_union = unary_union(land_geoms)

    # Create mask
    masked_data = log_data.copy()

    for i in range(len(lat)):
        for j in range(len(lon)):
            point = Point(lon[j], lat[i])
            if land_union.contains(point):
                masked_data[i, j] = np.nan

    # -------------------------------------------------

    fig = plt.figure(figsize=(6,6))
    ax = plt.axes(projection=ccrs.PlateCarree())

    ax.set_extent(
        [lon.min(), lon.max(), lat.min(), lat.max()],
        crs=ccrs.PlateCarree()
    )

    mesh = ax.pcolormesh(
        lon,
        lat,
        masked_data,
        cmap="viridis",
        shading="auto",
        vmin=0,
        vmax=1.2,
        transform=ccrs.PlateCarree()
    )

    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.coastlines(resolution="10m")

    cbar = plt.colorbar(mesh, ax=ax, shrink=0.7)
    cbar.set_label("log(1 + Chl)")

    ax.set_title(title)

    return fig