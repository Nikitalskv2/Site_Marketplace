import logging
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
        self.logger = logging.getLogger(__name__)

    def upload_article(self, article_id: int, content: str) -> str:
        key = f"articles/{article_id}.txt"
        try:
            self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=content)
            self.logger.info(f"Article {article_id} uploaded to {key}")
            return key
        except ClientError as e:
            self.logger.error(f"Failed to upload article {article_id}: {e}")
            raise RuntimeError(f"Failed to upload article: {e}")

    def get_article(self, key: str) -> Optional[str]:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            self.logger.info(f"Article fetched from {key}")
            return response["Body"].read().decode("utf-8")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                self.logger.warning(f"Article not found: {key}")
                return None
            self.logger.error(f"Failed to get article {key}: {e}")
            raise RuntimeError(f"Failed to get article: {e}")

    def delete_article(self, key: str):
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            self.logger.info(f"Article deleted from {key}")
        except ClientError as e:
            self.logger.error(f"Failed to delete article {key}: {e}")
            raise RuntimeError(f"Failed to delete article: {e}")
