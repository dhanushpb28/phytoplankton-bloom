import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.dates as mdates
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# =========================================================
# Helper utilities
# =========================================================
def _flatten_valid(*arrays):
    mask = np.ones_like(arrays[0], dtype=bool)
    for arr in arrays:
        mask &= ~np.isnan(arr)
    return [arr[mask] for arr in arrays]

def _current_speed(ds):
    return np.sqrt(ds.uo**2 + ds.vo**2)

def _format_dates(ax):
    """Fix crowded date axis"""
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
# =========================================================
# KPI CALCULATIONS (Executive dashboard style)
# =========================================================
# =========================================================
# EDUCATIONAL KPI ENGINE (interpretable indicators)
# =========================================================
def compute_kpis(ds, bloom_mask):

    # --- Raw metrics ---
    mean_chl = float(ds.chl.mean())
    bloom_coverage = float(bloom_mask.mean() * 100)
    sst = float(ds.sea_surface_temperature_anomaly.mean())
    current_speed = float(np.sqrt(ds.uo**2 + ds.vo**2).mean())
    nutrient_index = float((ds.no3.mean() + ds.po4.mean()) / 2)

    growth = float(ds.chl.diff("time").mean())

    # =====================================================
    # INTERPRETATION RULES (very important)
    # =====================================================

    def chl_status(x):
        if x < 1: return "Low"
        if x < 2: return "Moderate"
        return "High"

    def coverage_status(x):
        if x < 10: return "Localized"
        if x < 30: return "Regional"
        return "Widespread"

    def growth_status(x):
        if x < -0.02: return "Declining"
        if x < 0.02: return "Stable"
        return "Expanding"

    def sst_status(x):
        if x < -0.3: return "Cooling"
        if x < 0.3: return "Normal"
        return "Warming"

    def nutrient_status(x):
        if x < 0.5: return "Low"
        if x < 1.0: return "Moderate"
        return "Rich"

    def current_status(x):
        if x < 0.15: return "Weak Spread"
        if x < 0.35: return "Moderate Spread"
        return "Fast Spread"

    # =====================================================
    # FINAL KPI DICTIONARY
    # =====================================================
    return {
        "Bloom Intensity": f"{chl_status(mean_chl)} ({mean_chl:.2f})",
        "Bloom Coverage": f"{coverage_status(bloom_coverage)} ({bloom_coverage:.1f}%)",
        "Bloom Trend": f"{growth_status(growth)} ({growth:.3f})",
        "Ocean Temperature": f"{sst_status(sst)} ({sst:.2f}°C)",
        "Nutrient Availability": f"{nutrient_status(nutrient_index)} ({nutrient_index:.2f})",
        "Bloom Spread Risk": f"{current_status(current_speed)} ({current_speed:.2f} m/s)"
    }

# =========================================================
# Multi-line environmental trend (dashboard style)
# =========================================================
def plot_multivariate_trend(ds):

    chl  = ds.chl.mean(dim=["latitude","longitude"])
    phyc = ds.phyc.mean(dim=["latitude","longitude"])
    no3  = ds.no3.mean(dim=["latitude","longitude"])
    po4  = ds.po4.mean(dim=["latitude","longitude"])
    sst  = ds.sea_surface_temperature_anomaly.mean(dim=["latitude","longitude"])

    fig, ax = plt.subplots(figsize=(10,4))

    ax.plot(ds.time, chl,  label="Chl")
    ax.plot(ds.time, phyc, label="Phyc")
    ax.plot(ds.time, no3,  label="NO3")
    ax.plot(ds.time, po4,  label="PO4")
    ax.plot(ds.time, sst,  label="SST")

    _format_dates(ax)
    ax.legend(ncol=5)
    ax.set_title("Multivariate Environmental Trend")

    return fig

# =========================================================
# 1️⃣ Bloom coverage vs time + biological drivers
# =========================================================
def plot_bloom_timeseries(ds, bloom_mask):

    coverage = bloom_mask.mean(dim=["latitude","longitude"]) * 100

    chl_mean  = ds.chl.mean(dim=["latitude","longitude"])
  
    fig, ax1 = plt.subplots(figsize=(9,4))

    ax1.plot(ds.time, coverage, label="Bloom coverage (%)", linewidth=2)
    ax1.set_ylabel("Coverage %")

    ax2 = ax1.twinx()
    ax2.plot(ds.time, chl_mean,  label="Chl",  color="red")
    
    ax2.set_ylabel("Mean concentration")

    _format_dates(ax1)

    ax1.set_title("Bloom Coverage & Biological Drivers Over Time")
    fig.legend(loc="upper right")

    return fig

# =========================================================
# 2️⃣ Environmental drivers vs time
# =========================================================
def plot_environment_timeseries(ds):

    chl  = ds.chl.mean(dim=["latitude","longitude"])
    no3  = ds.no3.mean(dim=["latitude","longitude"])
    po4  = ds.po4.mean(dim=["latitude","longitude"])
    sst  = ds.sea_surface_temperature_anomaly.mean(dim=["latitude","longitude"])

    fig, ax = plt.subplots(figsize=(9,4))

    ax.plot(ds.time, chl,  label="Chlorophyll")
    ax.plot(ds.time, no3,  label="Nitrate")
    ax.plot(ds.time, po4,  label="Phosphate")
    ax.plot(ds.time, sst,  label="SST anomaly")

    _format_dates(ax)

    ax.legend()
    ax.set_title("Environmental Drivers Over Time")

    return fig

# =========================================================
# 3️⃣ Regional bloom analysis
# =========================================================
def plot_regional_bloom(ds):

    lat_mid = float(ds.latitude.mean())
    lon_mid = float(ds.longitude.mean())

    regions = {
        "North": ds.sel(latitude=slice(lat_mid, None)),
        "South": ds.sel(latitude=slice(None, lat_mid)),
        "East":  ds.sel(longitude=slice(lon_mid, None)),
        "West":  ds.sel(longitude=slice(None, lon_mid)),
    }

    means = [float(r.chl.mean()) for r in regions.values()]

    fig, ax = plt.subplots()
    ax.bar(regions.keys(), means)
    ax.set_title("Regional Bloom Intensity")
    ax.set_ylabel("Mean Chlorophyll")

    return fig



# =========================================================
# 5️⃣ Correlation matrix
# =========================================================
def plot_correlation_matrix(ds):

    speed = _current_speed(ds)

    df = pd.DataFrame({
        "chl": ds.chl.values.flatten(),
        "phyc": ds.phyc.values.flatten(),
        "nppv": ds.nppv.values.flatten(),
        "no3": ds.no3.values.flatten(),
        "po4": ds.po4.values.flatten(),
        "sst": ds.sea_surface_temperature_anomaly.values.flatten(),
        "current_speed": speed.values.flatten(),
    }).dropna()

    corr = df.corr()

    fig, ax = plt.subplots(figsize=(6,5))
    sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
    ax.set_title("Environmental Correlation Matrix")

    return fig

# =========================================================
# 6️⃣ Scatter relationships
# =========================================================
def plot_driver_scatter(ds):

    speed = _current_speed(ds)

    chl, no3, sst = _flatten_valid(
        ds.chl.values.flatten(),
        ds.no3.values.flatten(),
        ds.sea_surface_temperature_anomaly.values.flatten()
    )

    fig, axes = plt.subplots(1,3, figsize=(12,4))

    axes[0].scatter(no3, chl, s=2)
    axes[0].set_title("Chl vs Nitrate")

    axes[1].scatter(sst, chl, s=2)
    axes[1].set_title("Chl vs SST")

    axes[2].scatter(speed.values.flatten(), ds.chl.values.flatten(), s=2)
    axes[2].set_title("Chl vs Currents")

    return fig

# =========================================================
# 7️⃣ Bloom growth distribution
# =========================================================
def plot_growth_distribution(ds):

    growth = ds.chl.diff("time").values.flatten()
    growth = growth[~np.isnan(growth)]

    fig, ax = plt.subplots()
    ax.hist(growth, bins=40)
    ax.set_title("Bloom Growth Rate Distribution")
    ax.set_xlabel("Δ Chlorophyll")

    return fig
