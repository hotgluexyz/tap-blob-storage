#!/usr/bin/env python3
import os
import json
import argparse
import logging

from azure.storage.blob import BlobServiceClient

logger = logging.getLogger("tap-cloud-storage")
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def load_json(path):
    with open(path) as f:
        return json.load(f)


def parse_args():
    '''Parse standard command-line args.
    Parses the command-line arguments mentioned in the SPEC and the
    BEST_PRACTICES documents:
    -c,--config     Config file
    Returns the parsed args object from argparse. For each argument that
    point to JSON files (config, state, properties), we will automatically
    load and parse the JSON file.
    '''
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c', '--config',
        help='Config file',
        required=True)

    args = parser.parse_args()
    if args.config:
        setattr(args, 'config_path', args.config)
        args.config = load_json(args.config)

    return args


def download(args):
    logger.debug(f"Downloading data...")
    config = args.config
    container_name = config['container']
    connection_string = config['connect_string']
    path_prefix = config.get('path_prefix', "/")
    target_dir = config.get('target_dir', ".")

    # Upload all data in input_path to Google Cloud Storage
    blob_client = BlobServiceClient.from_connection_string(connection_string)
    container_client=blob_client.get_container_client(container_name)

    blob_list = container_client.list_blobs(name_starts_with=path_prefix)

    for blob in blob_list:
        file_name = blob.name.split('/')[-1]
        bytes = container_client.get_blob_client(blob).download_blob().readall()
        download_file_path = os.path.join(target_dir, file_name)
        
        logger.debug(f"Downloading: {blob.name} -> {download_file_path}")
    
        with open(download_file_path, "wb") as file:
            file.write(bytes)


def main():
    # Parse command line arguments
    args = parse_args()
    download(args)


if __name__ == "__main__":
    main()
