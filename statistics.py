def bloom_stats(bloom_mask, chl):
    return {
        "Coverage (%)": float(bloom_mask.mean()) * 100,
        "Max Chlorophyll": float(chl.max()),
        "Mean Chlorophyll": float(chl.mean())
    }
