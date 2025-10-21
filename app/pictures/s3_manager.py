from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

class S3Manager:
    def __init__(
            self,
            s3_key_id: str,
            s3_secret_key: str,
            s3_bucket_name: str,
            region_name: str = "ru-central1",
            endpoint_url: Optional[str] = None
    ):
        self.s3_bucket_name = s3_bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=s3_key_id,
            aws_secret_access_key=s3_secret_key,
            region_name=region_name,
            endpoint_url=endpoint_url
        )

    def upload_file(self, path: str, s3_key: str) -> bool:
        try:
            self.s3_client.upload_file(
                path,
                self.s3_bucket_name,
                s3_key,
                ExtraArgs={'ContentType': 'image/png'}
            )
            print(f"Файл {path} загружен в S3 как {s3_key}")
            return True
        except ClientError as e:
            print(f"Ошибка загрузки в S3: {e}")
            return False

    def delete_file(self, s3_key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket_name, Key=s3_key)
            print(f"Файл {s3_key} удален из S3")
            return True
        except ClientError as e:
            print(f"Ошибка удаления из S3: {e}")
            return False

    def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.s3_bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Ошибка генерации URL: {e}")
            return None

s3_manager = S3Manager(
    s3_key_id=settings.S3_KEY_ID,
    s3_secret_key=settings.S3_SECRET_KEY,
    s3_bucket_name=settings.S3_BUCKET_NAME,
    endpoint_url="https://storage.yandexcloud.net"
)