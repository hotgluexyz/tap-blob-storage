"""Azure Blob Storage authentication and client setup."""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from azure.core.exceptions import ClientAuthenticationError, HttpResponseError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient
from hotglue_etl_exceptions import InvalidCredentialsError

logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

# Azure SDK parse_connection_str messages. Match these only; do not wrap other ValueErrors.
_CONNECTION_STRING_ERRORS = (
    "Connection string is either blank or malformed.",
    "Connection string missing required connection details.",
    "Connection string specifies only secondary endpoint.",
)


def is_connection_string_error(error: ValueError) -> bool:
    """Return True when the Azure SDK rejected the connection string itself."""
    message = str(error)
    return any(known in message for known in _CONNECTION_STRING_ERRORS)


def _raise_invalid_credentials(error: Exception, message: Optional[str] = None) -> None:
    """Raise InvalidCredentialsError, preserving the original exception."""
    raise InvalidCredentialsError(
        message or f"Invalid Azure Storage credentials: {error}"
    ) from error


@contextmanager
def _azure_auth_errors(container_name: str) -> Iterator[None]:
    """Map Azure auth and container-access failures to InvalidCredentialsError."""
    try:
        yield
    except InvalidCredentialsError:
        raise
    except ValueError as error:
        if is_connection_string_error(error):
            _raise_invalid_credentials(error)
        raise
    except ClientAuthenticationError as error:
        _raise_invalid_credentials(error)
    except ResourceNotFoundError as error:
        _raise_invalid_credentials(
            error,
            f"Azure Blob Storage container '{container_name}' was not found.",
        )
    except HttpResponseError as error:
        if error.status_code in (401, 403):
            _raise_invalid_credentials(error)
        if error.status_code == 404:
            _raise_invalid_credentials(
                error,
                f"Azure Blob Storage container '{container_name}' was not found.",
            )
        raise


def get_container_client(config: Dict[str, Any]):
    """Create a container client and fail if credentials or the container are invalid."""
    container_name = config["container"]
    with _azure_auth_errors(container_name):
        blob_client = BlobServiceClient.from_connection_string(config["connect_string"])
        container_client = blob_client.get_container_client(container_name)
        if not container_client.exists():
            raise InvalidCredentialsError(
                f"Azure Blob Storage container '{container_name}' was not found."
            )
        return container_client
