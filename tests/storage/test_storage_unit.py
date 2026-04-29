from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from minio.error import S3Error

from libs.common.storage import (
    BucketNotFoundError,
    ObjectDownloadError,
    ObjectNotFoundError,
    ObjectUploadError,
    StorageClient,
    StorageError,
)

BUCKET = "test-bucket"
ENDPOINT = "localhost:9000"


def _make_s3error(code: str) -> S3Error:
    err = S3Error.__new__(S3Error)
    err.code = code
    err._message = code
    err.message = code
    err.resource = None
    err.request_id = None
    err.host_id = None
    err.response = None
    err.bucket_name = BUCKET
    err.object_name = None
    return err


def _client() -> StorageClient:
    return StorageClient(ENDPOINT, "key", "secret", BUCKET, secure=False)


# --- uri ---

def test_uri_format():
    c = _client()
    assert c.uri("raw_audio/abc/input.wav") == f"s3://{BUCKET}/raw_audio/abc/input.wav"


# --- put (bytes) ---

def test_put_bytes_calls_put_object():
    with patch("libs.common.storage.Minio") as MockMinio:
        mock_instance = MockMinio.return_value
        c = _client()
        data = b"hello"
        c.put("some/key.wav", data, content_type="audio/wav")
        args, kwargs = mock_instance.put_object.call_args
        assert args[0] == BUCKET
        assert args[1] == "some/key.wav"
        assert isinstance(args[2], io.BytesIO)
        assert args[3] == len(data)
        assert kwargs.get("content_type") == "audio/wav"


def test_put_file_calls_fput_object(tmp_path):
    with patch("libs.common.storage.Minio") as MockMinio:
        mock_instance = MockMinio.return_value
        c = _client()
        f = tmp_path / "audio.wav"
        f.write_bytes(b"data")
        c.put("some/key.wav", f, content_type="audio/wav")
        mock_instance.fput_object.assert_called_once_with(
            BUCKET, "some/key.wav", str(f), content_type="audio/wav"
        )


def test_put_returns_uri():
    with patch("libs.common.storage.Minio"):
        c = _client()
        result = c.put("some/key", b"data")
        assert result == f"s3://{BUCKET}/some/key"


def test_put_wraps_s3error_as_upload_error():
    with patch("libs.common.storage.Minio") as MockMinio:
        MockMinio.return_value.put_object.side_effect = _make_s3error("InternalError")
        c = _client()
        with pytest.raises(ObjectUploadError):
            c.put("key", b"data")


# --- exists ---

def test_exists_true_when_stat_succeeds():
    with patch("libs.common.storage.Minio") as MockMinio:
        MockMinio.return_value.stat_object.return_value = MagicMock()
        c = _client()
        assert c.exists("some/key") is True


def test_exists_false_on_no_such_key():
    with patch("libs.common.storage.Minio") as MockMinio:
        MockMinio.return_value.stat_object.side_effect = _make_s3error("NoSuchKey")
        c = _client()
        assert c.exists("some/key") is False


def test_exists_raises_on_unexpected_s3error():
    with patch("libs.common.storage.Minio") as MockMinio:
        MockMinio.return_value.stat_object.side_effect = _make_s3error("InternalError")
        c = _client()
        with pytest.raises(StorageError):
            c.exists("some/key")


# --- get_to_file ---

def test_get_to_file_calls_fget_object(tmp_path):
    with patch("libs.common.storage.Minio") as MockMinio:
        c = _client()
        dest = tmp_path / "out.wav"
        c.get_to_file("some/key", dest)
        MockMinio.return_value.fget_object.assert_called_once_with(BUCKET, "some/key", str(dest))


def test_get_to_file_raises_not_found(tmp_path):
    with patch("libs.common.storage.Minio") as MockMinio:
        MockMinio.return_value.fget_object.side_effect = _make_s3error("NoSuchKey")
        c = _client()
        with pytest.raises(ObjectNotFoundError):
            c.get_to_file("missing/key", tmp_path / "out.wav")


def test_get_to_file_raises_download_error(tmp_path):
    with patch("libs.common.storage.Minio") as MockMinio:
        MockMinio.return_value.fget_object.side_effect = _make_s3error("InternalError")
        c = _client()
        with pytest.raises(ObjectDownloadError):
            c.get_to_file("some/key", tmp_path / "out.wav")


# --- ensure_bucket ---

def test_ensure_bucket_creates_when_absent():
    with patch("libs.common.storage.Minio") as MockMinio:
        MockMinio.return_value.bucket_exists.return_value = False
        c = _client()
        c.ensure_bucket(create_if_missing=True)
        MockMinio.return_value.make_bucket.assert_called_once_with(BUCKET)


def test_ensure_bucket_skips_when_present():
    with patch("libs.common.storage.Minio") as MockMinio:
        MockMinio.return_value.bucket_exists.return_value = True
        c = _client()
        c.ensure_bucket(create_if_missing=True)
        MockMinio.return_value.make_bucket.assert_not_called()


def test_ensure_bucket_raises_when_absent_no_create():
    with patch("libs.common.storage.Minio") as MockMinio:
        MockMinio.return_value.bucket_exists.return_value = False
        c = _client()
        with pytest.raises(BucketNotFoundError):
            c.ensure_bucket(create_if_missing=False)
