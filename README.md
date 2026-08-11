# tap-blob-storage

`tap-blob-storage` is a Singer tap for [Azure Blob Storage](https://azure.microsoft.com/en-us/products/storage/blobs/), a cloud object storage service.

Built with the [Hotglue Singer SDK](https://github.com/hotgluexyz/HotglueSingerSDK) for Singer Taps.

This is a file-based tap. It downloads blobs from a container into a local directory. It does not emit Singer RECORD messages.

## Installation

```bash
pip install tap-blob-storage
```

Or install directly from the repository:

```bash
pip install git+https://github.com/hotgluexyz/tap-blob-storage.git
```

## Configuration

### Accepted Config Options

| Setting | Required | Description |
|---|---|---|
| `connect_string` | Yes | Azure Storage connection string |
| `container` | Yes | Blob container name |
| `path_prefix` | No | Optional blob name prefix filter. Defaults to empty string |
| `target_dir` | Yes | Local directory where downloaded files are written |
| `incremental_mode` | No | When true, sync only new or modified blobs using a state file |

Example `config.json`:

```json
{
  "connect_string": "DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net",
  "container": "maincontainer",
  "path_prefix": "reports/",
  "target_dir": "./data",
  "incremental_mode": false
}
```

In hotglue jobs, `target_dir` and formatted `path_prefix` are injected by the executor.

### Source Authentication and Authorization

This tap uses an Azure Storage **connection string**. You can copy it from the Azure Portal under **Storage account → Access keys**.

The service account needs at least read/list access on the target container.

## Usage

```bash
tap-blob-storage --version
tap-blob-storage --help
tap-blob-storage --about
tap-blob-storage --config config.json
tap-blob-storage --config config.json --state state.json
```

When `incremental_mode` is true, pass `--state` so the tap can read and update bookmarks.

Downloaded files use the blob basename only. For example, `reports/2024/file.csv` is saved as `file.csv`.

### Incremental State Format

```json
{
  "bookmarks": {
    "reports/file.csv": {
      "replication_key": "last_modified",
      "replication_key_value": "2026-08-11T19:25:06+00:00"
    }
  }
}
```

## Developer Resources

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
tox
```
