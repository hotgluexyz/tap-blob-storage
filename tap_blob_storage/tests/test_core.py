"""Tests for tap-blob-storage."""

from datetime import datetime, timezone

import pytest
from hotglue_etl_exceptions import InvalidCredentialsError
from hotglue_singer_sdk.testing import get_standard_tap_tests

from tap_blob_storage.auth import get_container_client, is_connection_string_error
from tap_blob_storage.client import should_download_blob
from tap_blob_storage.tap import TapBlobStorage

SAMPLE_CONFIG = {
    "connect_string": "DefaultEndpointsProtocol=https;AccountName=placeholder;AccountKey=placeholder;EndpointSuffix=core.windows.net",
    "container": "placeholder",
    "target_dir": "/tmp",
}


def test_standard_tap_tests():
    tests = get_standard_tap_tests(TapBlobStorage, config=SAMPLE_CONFIG)
    for test in tests:
        test()


def test_should_download_blob_without_bookmark():
    last_modified = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
    assert should_download_blob("sample.json", last_modified, {}) is True


def test_should_download_blob_when_remote_is_newer():
    last_modified = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
    bookmarks = {
        "sample.json": {
            "replication_key": "last_modified",
            "replication_key_value": "2026-08-11T11:00:00+00:00",
        }
    }
    assert should_download_blob("sample.json", last_modified, bookmarks) is True


def test_should_skip_blob_when_remote_is_unchanged():
    last_modified = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
    bookmarks = {
        "sample.json": {
            "replication_key": "last_modified",
            "replication_key_value": last_modified.isoformat(),
        }
    }
    assert should_download_blob("sample.json", last_modified, bookmarks) is False


def test_is_connection_string_error_matches_azure_parse_messages():
    assert is_connection_string_error(ValueError("Connection string is either blank or malformed."))
    assert is_connection_string_error(ValueError("Connection string missing required connection details."))
    assert is_connection_string_error(ValueError("Connection string specifies only secondary endpoint."))


def test_is_connection_string_error_ignores_unrelated_value_errors():
    assert not is_connection_string_error(ValueError("invalid literal for int()"))
    assert not is_connection_string_error(ValueError("target_dir is required"))


def test_malformed_connect_string_raises_invalid_credentials():
    with pytest.raises(InvalidCredentialsError, match="Connection string is either blank or malformed"):
        get_container_client(
            {
                "connect_string": "not-a-valid-connection-string",
                "container": "placeholder",
            }
        )
