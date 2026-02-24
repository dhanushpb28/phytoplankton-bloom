# =========================================================
# FORECAST MODEL MODULE (Production Ready)
# =========================================================

import os
import numpy as np
import tensorflow as tf
import json
from tensorflow.keras import layers
from tensorflow.keras.utils import register_keras_serializable

# =========================================================
# PATH HANDLING (Docker-safe)
# =========================================================

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "best_convlstm_model.keras")
STATS_PATH = os.path.join(BASE_DIR, "normalization_stats.json")

# =========================================================
# LOAD NORMALIZATION STATS
# =========================================================

with open(STATS_PATH, "r") as f:
    stats = json.load(f)

FEATURES = [
    "chl", "phyc", "nppv", "no3", "po4",
    "sea_surface_temperature_anomaly", "uo", "vo"
]

LOG_VARS = ["chl", "phyc", "nppv", "no3", "po4"]

# =========================================================
# CUSTOM LAYERS (Required for Model Loading)
# =========================================================

@register_keras_serializable()
class SpatialAttention(layers.Layer):
    def build(self, input_shape):
        self.conv = layers.Conv3D(
            filters=1,
            kernel_size=(1, 3, 3),
            padding="same",
            activation="sigmoid"
        )
        super().build(input_shape)

    def call(self, x):
        attention = self.conv(x)
        return x * attention


@register_keras_serializable()
def masked_mse(y_true, y_pred):
    return tf.reduce_mean((y_true - y_pred) ** 2)


# =========================================================
# LOAD MODEL (Cached)
# =========================================================

_model = None

def load_forecast_model():
    global _model
    if _model is None:
        _model =tf.keras.models.load_model(
            MODEL_PATH,
            custom_objects={
                "SpatialAttention": SpatialAttention,
                "masked_mse": masked_mse
            }
        )
    return _model


# =========================================================
# PREPROCESS STREAMLIT DATASET
# =========================================================

def preprocess_dataset(ds):
    """
    Must exactly match 02_preprocess_normalize.py
    """

    data_list = []

    for var in FEATURES:

        if var not in ds:
            raise ValueError(f"{var} missing from dataset")

        arr = ds[var]

        # Remove depth dimension if exists
        if "depth" in arr.dims:
            arr = arr.isel(depth=0)

        # Remove time dimension if single day object
        arr = arr.values

        # 1️⃣ LOG TRANSFORM (same as training)
        if var in LOG_VARS:
            arr = np.log1p(arr)

        # 2️⃣ FILL NaNs with 0 (CRITICAL — you missed this)
        arr = np.nan_to_num(arr, nan=0.0)

        # 3️⃣ NORMALIZE using saved stats
        mean = stats[var]["mean"]
        std = stats[var]["std"]

        arr = (arr - mean) / (std + 1e-8)

        data_list.append(arr)

    data = np.stack(data_list, axis=-1)

    return data

# =========================================================
# GENERATE FORECAST
# =========================================================

def generate_forecast(ds):
    """
    Generate 2-day chlorophyll forecast
    Requires at least 4 days in ds
    Returns:
        day1_map (H,W)
        day2_map (H,W)
    """

    if ds.time.size < 4:
        raise ValueError("At least 4 days required for forecasting.")

    model = load_forecast_model()

    data = preprocess_dataset(ds)

    # Use last 4 days
    input_seq = data[-4:]
    input_seq = np.expand_dims(input_seq, axis=0)

    prediction = model.predict(input_seq, verbose=0)[0]

    # Convert back to original chlorophyll scale
    chl_mean = stats["chl"]["mean"]
    chl_std = stats["chl"]["std"]

    day1 = prediction[0, :, :, 0] * chl_std + chl_mean
    day2 = prediction[1, :, :, 0] * chl_std + chl_mean

    # Physical constraint (chlorophyll cannot be negative)
    day1 = np.clip(day1, 0, None)
    day2 = np.clip(day2, 0, None)

    return day1, day2