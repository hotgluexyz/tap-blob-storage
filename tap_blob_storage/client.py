"""Azure Blob Storage download utilities."""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from tap_blob_storage.auth import get_container_client

logger = logging.getLogger("tap-blob-storage")

REPLICATION_KEY = "last_modified"


def _parse_replication_timestamp(value: str) -> datetime:
    """Parse a bookmark timestamp and default naive values to UTC."""
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp


def should_download_blob(blob_name: str, last_modified: datetime, bookmarks: Dict[str, Any]) -> bool:
    """Return True when a blob should be downloaded in incremental mode."""
    bookmark = bookmarks.get(blob_name) or {}
    stored_value = bookmark.get("replication_key_value")
    if not stored_value:
        return True
    return last_modified > _parse_replication_timestamp(stored_value)


def _download_blob(container_client, blob_name: str, target_path: str) -> None:
    """Download a single blob to the local target path."""
    blob_client = container_client.get_blob_client(blob_name)
    data = blob_client.download_blob().readall()
    with open(target_path, "wb") as file:
        file.write(data)


def _download_if_updated(
    container_client,
    blob_name: str,
    last_modified: datetime,
    bookmarks: Dict[str, Any],
    target_path: str,
) -> None:
    """Download a blob when it is new or newer than the stored bookmark."""
    if not should_download_blob(blob_name, last_modified, bookmarks):
        logger.info("%s being ignored... No updates", blob_name)
        return

    logger.info("Downloading incremental: %s -> %s", blob_name, target_path)
    _download_blob(container_client, blob_name, target_path)
    bookmarks[blob_name] = {
        "replication_key_value": last_modified.isoformat(),
        "replication_key": REPLICATION_KEY,
    }


def _load_state(state_path: Optional[str]) -> Dict[str, Any]:
    """Load incremental state, defaulting to an empty bookmarks map."""
    if state_path and os.path.exists(state_path):
        with open(state_path) as state_file:
            state = json.load(state_file)
    else:
        state = {}
    state.setdefault("bookmarks", {})
    return state


def _save_state(state_path: Optional[str], state: Dict[str, Any]) -> None:
    """Write incremental state when a state path was provided."""
    if not state_path:
        return
    with open(state_path, "w") as state_file:
        json.dump(state, state_file, indent=4)


def download(config: Dict[str, Any], state_path: Optional[str] = None) -> None:
    """Download blobs from Azure Blob Storage into target_dir."""
    logger.info("Downloading data...")
    path_prefix = config.get("path_prefix") or ""
    target_dir = config.get("target_dir", ".")
    incremental_mode = config.get("incremental_mode", False)

    os.makedirs(target_dir, exist_ok=True)
    container_client = get_container_client(config)
    state = _load_state(state_path) if incremental_mode else {"bookmarks": {}}

    for blob in container_client.list_blobs(name_starts_with=path_prefix):
        if blob.name.endswith("/"):
            continue

        target_path = os.path.join(target_dir, blob.name.split("/")[-1])
        if incremental_mode:
            _download_if_updated(
                container_client,
                blob.name,
                blob.last_modified,
                state["bookmarks"],
                target_path,
            )
        else:
            logger.info("Downloading: %s -> %s", blob.name, target_path)
            _download_blob(container_client, blob.name, target_path)

    logger.info("Data downloaded.")

    if incremental_mode:
        _save_state(state_path, state)
