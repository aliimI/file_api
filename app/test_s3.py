import boto3
from app.config import settings


s3 = boto3.client(
    "s3",
    region_name=settings.S3_REGION,
    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    
)

with open("test.txt", "rb") as f:
    s3.upload_fileobj(f, settings.S3_REGION, "test.txt")

print("Uploaded!")

resp = s3.list_objects_v2(Bucket=settings.S3_BUCKET)
print(resp.get("Contents"))