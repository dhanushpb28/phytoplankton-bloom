# =========================================================
# ENVIRONMENT SAFETY FOR HUGGING FACE (CRITICAL)
# =========================================================
import sys
import os
sys.path.append(os.path.dirname(__file__))

# =========================================================
# HF SAFE ENVIRONMENT SETUP
# =========================================================
import tempfile
tmp = tempfile.gettempdir()

os.environ["CARTOPY_DATA_DIR"] = os.path.join(tmp, "cartopy_data")
os.environ["CARTOPY_USER_BACKGROUNDS"] = os.path.join(tmp, "cartopy_bg")
os.environ["MPLCONFIGDIR"] = os.path.join(tmp, "mpl_config")
os.environ["STREAMLIT_HOME"] = os.path.join(tmp, "streamlit")
os.environ["HOME"] = tmp


for env in [
    "CARTOPY_DATA_DIR",
    "CARTOPY_USER_BACKGROUNDS",
    "MPLCONFIGDIR",
    "STREAMLIT_HOME",
]:
    os.makedirs(os.environ[env], exist_ok=True)

# =========================================================
# IMPORTS (LIGHTWEIGHT FIRST)
# =========================================================
import streamlit as st
import datetime

from utils.auth import copernicus_login
from data.loader import fetch_and_load
from data.detection import detect_bloom
from visualization.visualizer import plot_chl_bloom
from visualization.statistics import bloom_stats

# =========================================================
# STREAMLIT CONFIG
# =========================================================
st.set_page_config(
    page_title="Phytoplankton Bloom Dashboard",
    layout="wide"
)

st.title("🌊 AI-Based Phytoplankton Bloom Monitoring")
st.markdown(
    """
    Interactive dashboard for **detection and analysis of phytoplankton blooms**
    using **Copernicus Marine forecast data**.
    """
)

# =========================================================
# SIDEBAR — USER INPUTS (NOAA-STYLE)
# =========================================================
st.sidebar.header("🧭 Data Settings")

today = datetime.date.today()
selected_date = st.sidebar.date_input(
    "Select Date",
    value=today - datetime.timedelta(days=3)
)

lat_min = st.sidebar.number_input("Min Latitude", -60.0, 60.0, -50.0)
lat_max = st.sidebar.number_input("Max Latitude", -60.0, 60.0, -10.0)

lon_min = st.sidebar.number_input("Min Longitude", 0.0, 360.0, 100.0)
lon_max = st.sidebar.number_input("Max Longitude", 0.0, 360.0, 170.0)

threshold = st.sidebar.slider(
    "Bloom Threshold (mg/m³)",
    min_value=0.5,
    max_value=10.0,
    value=2.0,
    step=0.1
)

run = st.sidebar.button("🚀 Run Analysis")

# =========================================================
# MAIN EXECUTION — NOTHING RUNS BEFORE THIS
# =========================================================
if run and selected_date:

    with st.spinner("🔐 Logging in & fetching Copernicus data…"):
        # Login ONLY when required
        copernicus_login()

        ds = fetch_and_load(
            date=str(selected_date),
            lat_min=lat_min,
            lat_max=lat_max,
            lon_min=lon_min,
            lon_max=lon_max
        )


    # =====================================================
    # BLOOM DETECTION
    # =====================================================
    bloom_mask = detect_bloom(ds.chl, threshold)
    stats = bloom_stats(bloom_mask, ds.chl)

    # =====================================================
    # TABS
    # =====================================================
    tab1, tab2 = st.tabs(["📊 Detection Results", "📈 Statistics"])

    # ---------------- Detection Tab ----------------
    with tab1:
        st.subheader("Chlorophyll-a with Bloom Overlay")
        fig = plot_chl_bloom(ds, bloom_mask)
        st.pyplot(fig)

    # ---------------- Statistics Tab ----------------
    with tab2:
        st.subheader("Bloom Statistics")
        cols = st.columns(len(stats))
        for col, (k, v) in zip(cols, stats.items()):
            col.metric(k, round(v, 2))

else:
    st.info("👈 Set parameters and click **Run Analysis** to begin.")