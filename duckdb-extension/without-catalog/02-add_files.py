# Required:
#
#   pip install pyiceberg[sql-sqlite]

import os
from pyiceberg.catalog.memory import InMemoryCatalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    NestedField,
    DateType,
    StringType,
    DoubleType,
)
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.transforms import MonthTransform
from pyiceberg.exceptions import NamespaceAlreadyExistsError, TableAlreadyExistsError

catalog = InMemoryCatalog(
    name="default",
    warehouse=os.path.abspath("./warehouse"),
)

# In-memory で事前に作ってないので、NoSuchTableErrorで失敗する
table = catalog.load_table("sample.daily_sales")

table.add_files(file_paths=[
    "s3://kaoriya/daily_sales/daily_sales-202403.parquet"
    ])
