"""Azure Blob Storage tap class."""

from typing import List

from hotglue_singer_sdk import Stream, Tap
from hotglue_singer_sdk import typing as th
from hotglue_singer_sdk.helpers.capabilities import AlertingLevel

from tap_blob_storage.client import download


class TapBlobStorage(Tap):
    """Tap for importing files from Azure Blob Storage."""

    name = "tap-blob-storage"
    alerting_level = AlertingLevel.ERROR

    config_jsonschema = th.PropertiesList(
        th.Property(
            "connect_string",
            th.StringType,
            required=True,
            description="Azure Storage connection string.",
        ),
        th.Property(
            "container",
            th.StringType,
            required=True,
            description="Blob container name.",
        ),
        th.Property(
            "path_prefix",
            th.StringType,
            description="Optional blob name prefix filter.",
        ),
        th.Property(
            "target_dir",
            th.StringType,
            required=True,
            description="Local directory path where downloaded files are saved.",
        ),
        th.Property(
            "incremental_mode",
            th.BooleanType,
            description="Sync only new and modified files when a state file is provided.",
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        return []

    def register_state_from_file(self, state):
        """State is managed by the download client; skip SDK stream state loading."""

    def run_sync(self, catalog=None, state=None):
        download(dict(self.config), state_path=state)


if __name__ == "__main__":
    TapBlobStorage.cli()
