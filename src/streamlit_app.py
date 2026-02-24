# =========================================================
# ENVIRONMENT SAFETY
# =========================================================
import sys, os, tempfile

sys.path.append(os.path.dirname(__file__))

tmp = tempfile.gettempdir()
os.environ["CARTOPY_DATA_DIR"] = os.path.join(tmp, "cartopy_data")
os.environ["CARTOPY_USER_BACKGROUNDS"] = os.path.join(tmp, "cartopy_bg")
os.environ["MPLCONFIGDIR"] = os.path.join(tmp, "mpl_config")
os.environ["STREAMLIT_HOME"] = os.path.join(tmp, "streamlit")
os.environ["HOME"] = tmp

for env in ["CARTOPY_DATA_DIR","CARTOPY_USER_BACKGROUNDS","MPLCONFIGDIR","STREAMLIT_HOME"]:
    os.makedirs(os.environ[env], exist_ok=True)

# =========================================================
# IMPORTS
# =========================================================
import streamlit as st
import datetime
import numpy as np
from forecasting.forecast_model import generate_forecast
from visualization.visualizer import plot_forecast_map
from data.update_database import update_database
from data.s3_loader import load_from_s3
from data.detection import detect_bloom

from visualization.visualizer import (
    plot_chl_bloom,
    plot_mean_bloom_map,
    plot_variable_map,
    animate_variable,plot_environment_correlation,plot_bloom_timeseries,plot_bloom_risk_radar
)


# =========================================================
# STREAMLIT CONFIG
# =========================================================
st.set_page_config(page_title="Phytoplankton Bloom Dashboard", layout="wide")

st.title("🌊 Phytoplankton Bloom Monitoring System")
st.markdown(
    "Database-driven dashboard using **Copernicus Marine data stored in S3**."
)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.header("🗄 Database Control")

if st.sidebar.button("🔄 Update Database"):
    with st.spinner("Updating S3 database (Copernicus → S3)…"):
        msg = update_database()
    st.success(msg)

st.sidebar.header("🧭 Analysis Settings")

today = datetime.date.today()

start_date = st.sidebar.date_input("Start Date", today - datetime.timedelta(days=7))
end_date   = st.sidebar.date_input("End Date", today)

# ⭐ Default bounds now match Copernicus download region
lat_min = st.sidebar.number_input("Min Latitude", -60.0, 60.0, -45.0)
lat_max = st.sidebar.number_input("Max Latitude", -60.0, 60.0, -10.0)
lon_min = st.sidebar.number_input("Min Longitude", 0.0, 360.0, 110.0)
lon_max = st.sidebar.number_input("Max Longitude", 0.0, 360.0, 155.0)

threshold = st.sidebar.slider("Bloom Threshold (mg/m³)", 0.5, 10.0, 2.0, 0.1)
run = st.sidebar.button("🚀 Run Analysis")

# =========================================================
# LOAD DATA FROM S3
# =========================================================
if run:
    if start_date > end_date:
        st.error("❌ Start date must be before end date.")
        st.stop()

    with st.spinner("📥 Loading data from S3 database…"):
        ds = load_from_s3(start_date, end_date, lat_min, lat_max, lon_min, lon_max)

    st.session_state["dataset"] = ds

# =========================================================
# USE STORED DATA
# =========================================================
if "dataset" not in st.session_state:
    st.info("👈 Update database or run analysis to begin.")
    st.stop()

ds = st.session_state["dataset"]

# =========================================================
# BLOOM DETECTION
# =========================================================
bloom_mask = detect_bloom(ds.chl, threshold)

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Detection Results", "📈 Variable Analysis", "📋 Statistics", "🔮 Forecasting"]
)
# ---------------- TAB 1 ----------------
with tab1:
    st.subheader("Chlorophyll-a with Bloom Overlay (Latest Day)")
    st.pyplot(
        plot_chl_bloom(
            ds.isel(time=-1),
            bloom_mask.isel(time=-1),
            lat_min, lat_max, lon_min, lon_max
        )
    )

    st.subheader("Mean Bloom Intensity")
    st.pyplot(
        plot_mean_bloom_map(
            ds,
            threshold,
            lat_min, lat_max, lon_min, lon_max
        )
    )

# ---------------- TAB 2 ----------------
with tab2:
    variable = st.selectbox("Select Variable", ["chl", "phyc", "no3", "po4", "nppv","sea_surface_temperature_anomaly","uo", "vo"])

    st.pyplot(
        plot_variable_map(
            ds.isel(time=-1),
            variable,
            f"{variable.upper()} Map",
            lat_min, lat_max, lon_min, lon_max
        )
    )

    if st.button("▶ Generate Animation"):
        gif = animate_variable(
            ds,
            variable,
            lat_min, lat_max,
            lon_min, lon_max
        )
        st.image(gif)
# from visualization.statistics import (
#     plot_bloom_timeseries,
#     plot_environment_timeseries,
#     plot_regional_bloom,
#     plot_bloom_hotspots,
#     plot_correlation_matrix,
#     plot_driver_scatter
# )


# # ---------------- TAB 3 ----------------
# # ---------------- TAB 3 ----------------
# with tab3:

#     st.subheader("📊 Temporal Bloom Analysis")
#     st.pyplot(plot_bloom_timeseries(ds, bloom_mask))
#     st.pyplot(plot_environment_timeseries(ds))

#     st.subheader("🌍 Spatial Bloom Analysis")
#     st.pyplot(plot_regional_bloom(ds))
#     st.subheader("🔬 Environmental Drivers")
#     st.pyplot(plot_correlation_matrix(ds))
#     st.pyplot(plot_driver_scatter(ds))

from visualization.statistics import (
    compute_kpis,
    plot_bloom_timeseries,
    plot_environment_timeseries,
    plot_regional_bloom,
    plot_correlation_matrix,
    plot_driver_scatter,
    plot_multivariate_trend
)

# ---------------- TAB 3 ----------------
with tab3:

    # =====================================================
    # KPI ROW
    # =====================================================
    kpis = compute_kpis(ds, bloom_mask)

    st.markdown("## 🌊 Executive Bloom Dashboard")

    def kpi_color(text):
        if "High" in text or "Expanding" in text or "Warming" in text or "Rich" in text or "Fast" in text:
            return "🔴"
        if "Moderate" in text or "Regional" in text:
            return "🟡"
        return "🟢"

    k1,k2,k3 = st.columns(3)
    k4,k5,k6 = st.columns(3)
    cols = [k1,k2,k3,k4,k5,k6]

    descriptions = {
        "Bloom Intensity": "Average chlorophyll concentration in ocean",
        "Bloom Coverage": "Percentage of region affected by bloom",
        "Bloom Trend": "Is bloom increasing or decreasing",
        "Ocean Temperature": "Sea surface temperature anomaly",
        "Nutrient Availability": "Nutrients fueling phytoplankton growth",
        "Bloom Spread Risk": "Ocean currents transporting bloom"
    }

    for col,(k,v) in zip(cols, kpis.items()):
        col.markdown(f"### {kpi_color(v)} {k}")
        col.markdown(f"## {v}")
        col.caption(descriptions[k])

    st.divider()

    # =====================================================
    # TEMPORAL ANALYTICS
    # =====================================================
    st.markdown("## 📈 Temporal Bloom Analytics")

    col1,col2 = st.columns(2)
    col1.pyplot(plot_bloom_timeseries(ds, bloom_mask))
    col2.pyplot(plot_environment_timeseries(ds))

    st.pyplot(plot_multivariate_trend(ds))

    st.divider()

    # =====================================================
    # SPATIAL ANALYTICS
    # =====================================================
    st.markdown("## 🌍 Spatial Bloom Behaviour")

    st.pyplot(plot_regional_bloom(ds))

    st.divider()

    # =====================================================
    # ENVIRONMENTAL DRIVERS
    # =====================================================
    st.markdown("## 🔬 Environmental Relationships")

    col1,col2 = st.columns(2)
    col1.pyplot(plot_correlation_matrix(ds))
    col2.pyplot(plot_driver_scatter(ds))

with tab4:

    st.subheader("🔮 2-Day Chlorophyll Forecast")

    if ds.time.size < 4:
        st.warning("At least 4 days required for forecasting.")
    else:

        with st.spinner("Generating forecast..."):
            day1, day2 = generate_forecast(ds)

        lat = ds.latitude.values
        lon = ds.longitude.values

        next_day1 = ds.time.values[-1] + np.timedelta64(1,'D')
        next_day2 = ds.time.values[-1] + np.timedelta64(2,'D')

        col1, col2 = st.columns(2)

        col1.pyplot(
            plot_forecast_map(
                lat, lon,
                day1,
                f"Forecast - {str(next_day1)[:10]}"
            )
        )

        col2.pyplot(
            plot_forecast_map(
                lat, lon,
                day2,
                f"Forecast - {str(next_day2)[:10]}"
            )
        )