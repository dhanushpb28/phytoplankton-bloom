import boto3

BUCKET = "hab-bloom-db-2026"
PREFIX = "daily/"

s3 = boto3.resource("s3")
bucket = s3.Bucket(BUCKET)

print("Deleting objects...")

count = 0
for obj in bucket.objects.filter(Prefix=PREFIX):
    obj.delete()
    count += 1
    if count % 50 == 0:
        print(f"Deleted {count} files...")

print(f"\n✅ Done. Deleted {count} objects from {BUCKET}/{PREFIX}")
