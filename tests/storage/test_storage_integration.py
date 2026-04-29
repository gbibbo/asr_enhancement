from __future__ import annotations

import os
import uuid

import pytest

from libs.common.storage import ObjectNotFoundError, StorageClient

pytestmark = pytest.mark.skipif(
    not os.environ.get("MINIO_ENDPOINT"),
    reason="MINIO_ENDPOINT not set — skipping MinIO integration tests",
)


@pytest.fixture(scope="module")
def client() -> StorageClient:
    c = StorageClient(
        endpoint=os.environ["MINIO_ENDPOINT"],
        access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
        bucket=os.environ.get("MINIO_BUCKET", "asr-platform"),
        secure=os.environ.get("MINIO_SECURE", "false").lower() == "true",
    )
    c.ensure_bucket(create_if_missing=True)
    return c


def _key(suffix: str) -> str:
    return f"test/{uuid.uuid4()}/{suffix}"


def test_ensure_bucket_idempotent(client: StorageClient):
    client.ensure_bucket(create_if_missing=True)
    client.ensure_bucket(create_if_missing=True)


def test_put_bytes_and_exists(client: StorageClient):
    key = _key("bytes.bin")
    client.put(key, b"hello integration")
    assert client.exists(key) is True


def test_put_file_and_exists(client: StorageClient, tmp_path):
    key = _key("file.bin")
    f = tmp_path / "upload.bin"
    f.write_bytes(b"file content")
    client.put(key, f)
    assert client.exists(key) is True


def test_get_to_file_round_trip(client: StorageClient, tmp_path):
    data = b"round trip content"
    key = _key("roundtrip.bin")
    client.put(key, data)
    dest = tmp_path / "downloaded.bin"
    client.get_to_file(key, dest)
    assert dest.read_bytes() == data


def test_exists_false_for_missing_key(client: StorageClient):
    key = _key("does-not-exist.bin")
    assert client.exists(key) is False


def test_get_to_file_raises_for_missing_key(client: StorageClient, tmp_path):
    key = _key("also-does-not-exist.bin")
    with pytest.raises(ObjectNotFoundError):
        client.get_to_file(key, tmp_path / "out.bin")


def test_uri_matches_expected_format(client: StorageClient):
    bucket = os.environ.get("MINIO_BUCKET", "asr-platform")
    key = "raw_audio/test-id/input.wav"
    assert client.uri(key) == f"s3://{bucket}/{key}"
