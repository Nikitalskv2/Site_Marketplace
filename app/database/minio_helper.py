import boto3
from botocore.client import Config

# Конфигурация клиента
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="password",
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

# # Создание бакета
# bucket_name = "my-bucket"
# s3.create_bucket(Bucket=bucket_name)
# print(f"Bucket {bucket_name} created!")
#
# # Загрузка файла
# s3.upload_file("example.txt", bucket_name, "example.txt")
# print("File uploaded!")
#
# # Список объектов в бакете
# objects = s3.list_objects_v2(Bucket=bucket_name)
# print("Objects in bucket:")
# for obj in objects.get('Contents', []):
#     print(obj['Key'])
