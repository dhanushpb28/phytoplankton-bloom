import os
import copernicusmarine

def copernicus_login():
    copernicusmarine.login(
        username=os.getenv("COPERNICUS_USERNAME"),
        password=os.getenv("COPERNICUS_PASSWORD")
    )
