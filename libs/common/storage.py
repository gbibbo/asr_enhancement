from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING, Union

from minio import Minio
from minio.error import S3Error

if TYPE_CHECKING:
    from libs.common.settings import Settings


class StorageError(Exception):
    """Base class for all storage errors."""


class BucketNotFoundError(StorageError):
    """Bucket does not exist and create_if_missing=False."""


class ObjectUploadError(StorageError):
    """put() failed."""


class ObjectDownloadError(StorageError):
    """get_to_file() failed for a reason other than missing key."""


class ObjectNotFoundError(StorageError):
    """get_to_file() called on a key that does not exist."""


class StorageClient:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        self._bucket = bucket

    @classmethod
    def from_settings(cls, settings: "Settings") -> "StorageClient":
        return cls(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket,
            secure=settings.minio_secure,
        )

    def uri(self, key: str) -> str:
        return f"s3://{self._bucket}/{key}"

    def put(
        self,
        key: str,
        source: Union[bytes, Path],
        content_type: str = "application/octet-stream",
    ) -> str:
        try:
            if isinstance(source, Path):
                self._client.fput_object(self._bucket, key, str(source), content_type=content_type)
            else:
                buf = io.BytesIO(source)
                self._client.put_object(
                    self._bucket, key, buf, len(source), content_type=content_type
                )
        except S3Error as exc:
            raise ObjectUploadError(f"Upload failed for {key!r}: {exc}") from exc
        return self.uri(key)

    def get_to_file(self, key: str, dest: Path) -> None:
        try:
            self._client.fget_object(self._bucket, key, str(dest))
        except S3Error as exc:
            if exc.code == "NoSuchKey":
                raise ObjectNotFoundError(f"Object not found: {key!r}") from exc
            raise ObjectDownloadError(f"Download failed for {key!r}: {exc}") from exc

    def exists(self, key: str) -> bool:
        try:
            self._client.stat_object(self._bucket, key)
            return True
        except S3Error as exc:
            if exc.code == "NoSuchKey":
                return False
            raise StorageError(f"Existence check failed for {key!r}: {exc}") from exc

    def ensure_bucket(self, create_if_missing: bool = True) -> None:
        found = self._client.bucket_exists(self._bucket)
        if found:
            return
        if not create_if_missing:
            raise BucketNotFoundError(f"Bucket {self._bucket!r} does not exist")
        self._client.make_bucket(self._bucket)


def make_storage_client(settings: "Settings") -> StorageClient:
    return StorageClient.from_settings(settings)
