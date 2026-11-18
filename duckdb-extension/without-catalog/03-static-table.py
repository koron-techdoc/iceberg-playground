# Required:
#
#   pip install pyiceberg[sql-sqlite]

import os
from pyiceberg.table import StaticTable

table = static_table = StaticTable.from_metadata("./warehouse/sample/daily_sales/metadata/00001-066be5a8-dff6-45ae-8a25-f2c3eb7cebe6.metadata.json")

table.add_files(file_paths=[
    "s3://kaoriya/daily_sales/daily_sales-202403.parquet"
    ])
