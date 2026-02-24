import os
import copernicusmarine

def copernicus_login():
    """
    Non-interactive login using environment variables.
    Works with ALL current copernicusmarine versions.
    """
    user = os.getenv("COPERNICUS_USERNAME")
    pwd = os.getenv("COPERNICUS_PASSWORD")

    if not user or not pwd:
        raise RuntimeError(
            "Copernicus credentials not found in environment variables."
        )

    # ✅ Compatible with all released versions
    copernicusmarine.login(
        username=user,
        password=pwd
    )
