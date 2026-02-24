import boto3

BUCKET = "hab-bloom-db-2026"
s3 = boto3.client("s3")

def upload_to_s3(local_path, s3_key):
    s3.upload_file(local_path, BUCKET, s3_key)
    print(f"✅ Uploaded: s3://{BUCKET}/{s3_key}")
