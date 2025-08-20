import boto3

from app.config import settings

class S3Storage:
    def __init__(self):
        self.bucket = settings.S3_BUCKET
        self.client = boto3.client(
            "s3",
            region_name = settings.S3_REGION,
            aws_access_key_id = settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key = settings.S3_SECRET_ACCESS_KEY,
        )

    def presigned_put(self, *, key: str, expires_in: int = 3600, content_type: str | None):
        params = {"Bucket": self.bucket, "Key": key}
        if content_type:
            params["ContentType"] = content_type
        return self.client.generate_presigned_url("put_object", Params=params, ExpiresIn=expires_in)
    

    def presigned_get(self, *, key: str, expires_in: int = 3600) -> str:
        params = {"Bucket": self.bucket, "Key": key}

        return self.client.generate_presigned_url("get_object", Params=params, ExpiresIn=expires_in)
        

    # get metadata
    def head(self, *, key: str) -> dict:
        return self.client.head_object(Bucket=self.bucket, Key=key)
    
    def delete(self, *, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)