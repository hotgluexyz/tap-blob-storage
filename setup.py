#!/usr/bin/env python

from setuptools import setup

setup(
    name='tap-blob-storage',
    version='1.0.0',
    description='hotglue tap for importing data from Google Cloud Storage',
    author='hotglue',
    url='https://hotglue.xyz',
    classifiers=['Programming Language :: Python :: 3 :: Only'],
    py_modules=['tap_blob_storage'],
    install_requires=[
        'azure-storage-blob==12.8.1',
        'argparse==1.4.0'
    ],
    entry_points='''
        [console_scripts]
        tap-blob-storage=tap_blob_storage:main
    ''',
    packages=['tap_blob_storage']
)
