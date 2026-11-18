# Required:
#
#   pip install pyiceberg[sql-sqlite]

import os
from pyiceberg.catalog import load_catalog

catalog = load_catalog(
    "default",
    **{
        "uri": "sqlite:///./iceberg_catalog.db",
        "warehouse": "s3://kaoriya/warehouse/s3-direct",
    }
)

table = catalog.load_table("sample.daily_sales")

table.add_files(file_paths=[
    "s3://kaoriya/daily_sales/daily_sales-202403.parquet"
    ])
