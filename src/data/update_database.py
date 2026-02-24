from datetime import date, timedelta
from utils.auth import copernicus_login
from data.fetch_copernicus import fetch_daily_data
from data.upload_s3 import upload_to_s3
from data.s3_utils import get_last_available_date


LAT_MIN, LAT_MAX = -45, -10
LON_MIN, LON_MAX = 110, 155
DEFAULT_START_DATE = date(2026, 1, 1)

def update_database():
    copernicus_login()

    today = date.today()
    last_date = get_last_available_date()

    start_date = DEFAULT_START_DATE if last_date is None else last_date + timedelta(days=1)

    if start_date > today:
        return "✅ Database already up-to-date"

    current = start_date
    while current <= today:
        print(f"📥 Downloading {current} ...")

        files = fetch_daily_data(
            str(current), LAT_MIN, LAT_MAX, LON_MIN, LON_MAX
        )

        y, m, d = current.strftime("%Y/%m/%d").split("/")
        for name, path in files.items():
            key = f"daily/{y}/{m}/{d}/{name}.nc"
            upload_to_s3(path, key)

        current += timedelta(days=1)

    return f"✅ Database updated through {today}"
