import boto3
from datetime import date

BUCKET = "hab-bloom-db-2026"
PREFIX = "daily/"

s3 = boto3.client("s3")

def get_last_available_date():
    """
    Returns latest date available in S3 as datetime.date
    """
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    if "Contents" not in resp:
        return None

    dates = set()
    for obj in resp["Contents"]:
        parts = obj["Key"].split("/")
        # daily/YYYY/MM/DD/file.nc
        if len(parts) >= 4:
            try:
                y, m, d = map(int, parts[1:4])
                dates.add(date(y, m, d))
            except:
                pass

    return max(dates) if dates else None
