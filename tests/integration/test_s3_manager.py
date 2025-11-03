import pytest
from moto import mock_aws
import boto3

pytestmark = pytest.mark.integration

@mock_aws
def test_s3_manager_presign_and_delete():
    region = "us-east-1"
    bucket = "test-bucket"
    s3 = boto3.client("s3", region_name=region)
    s3.create_bucket(Bucket=bucket)
    s3.put_object(Bucket=bucket, Key="pictures/pic.png", Body=b"123")

    from app.pictures.s3_manager import S3Manager
    m = S3Manager(
        s3_key_id="test",
        s3_secret_key="test",
        s3_bucket_name=bucket,
        region_name=region,
        endpoint_url=None,
    )

    url = m.get_presigned_url("pictures/pic.png", expiration=600)
    assert isinstance(url, str) and url.startswith("http")

    ok = m.delete_file("pictures/pic.png")
    assert ok is True