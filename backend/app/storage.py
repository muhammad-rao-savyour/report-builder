"""S3 access.

Locally this points at MinIO. On AWS the two endpoint settings are empty and
boto3 talks to real S3, picking up credentials from the EC2 IAM role. The code
does not change. You will never put an AWS key in this file.

Why two clients: inside Docker, storage is reachable at http://minio:9000, but
your browser cannot resolve that name. So URLs we hand to the browser must be
signed with the address the browser can reach (localhost). On AWS both are the
same, so this problem disappears.
"""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from .config import settings

_cfg = Config(signature_version="s3v4", retries={"max_attempts": 5, "mode": "standard"})


def _client(endpoint: str):
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=endpoint or None,
        config=_cfg,
    )


internal = _client(settings.s3_endpoint)
browser_facing = _client(settings.s3_public_endpoint or settings.s3_endpoint)


def presigned_put_url(key: str, expires: int = 3600) -> str:
    """A one-hour permission slip. The file goes browser -> S3 directly.

    It never passes through your API. This is the whole trick for large files:
    a 2 GB upload uses zero API memory and zero API bandwidth, so one small
    server can accept a hundred of them at once.
    """
    return browser_facing.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires,
    )


def open_stream(key: str):
    """Return a file-like object. Nothing is downloaded yet.

    Bytes arrive only as you read them, so memory stays flat no matter how big
    the file is.
    """
    return internal.get_object(Bucket=settings.s3_bucket, Key=key)["Body"]


def object_exists(key: str) -> bool:
    """Is the file actually in storage?

    head_object asks for the metadata only, not the bytes, so this is cheap
    even for a 2 GB file.
    """
    try:
        internal.head_object(Bucket=settings.s3_bucket, Key=key)
        return True
    except ClientError as err:
        if err.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
            return False
        raise
