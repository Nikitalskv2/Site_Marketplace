from typing import Optional

import boto3
from botocore.exceptions import ClientError


class S3Repository:
    def __init__(
        self, endpoint_url: str, access_key: str, secret_key: str, bucket_name: str
    ):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self.bucket_name = bucket_name

    def upload_article(self, article_id: int, content: str) -> str:
        """Загрузка статьи в MinIO."""
        key = f"articles/{article_id}.txt"
        try:
            self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=content)
            return key
        except ClientError as e:
            raise RuntimeError(f"Failed to upload article: {e}")

    def get_article(self, key: str) -> Optional[str]:
        """Получение статьи из MinIO."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read().decode("utf-8")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise RuntimeError(f"Failed to get article: {e}")

    def delete_article(self, key: str):
        """Удаление статьи из MinIO."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            raise RuntimeError(f"Failed to delete article: {e}")
