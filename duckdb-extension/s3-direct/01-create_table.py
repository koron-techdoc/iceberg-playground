# Required:
#
#   pip install pyiceberg[sql-sqlite]

import os
from pyiceberg.catalog import load_catalog
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

catalog = load_catalog(
    "default",
    **{
        "uri": "sqlite:///./iceberg_catalog.db",
        "warehouse": "s3://kaoriya/warehouse/s3-direct",
    }
)

try:
    catalog.create_namespace("sample")
except NamespaceAlreadyExistsError:
    pass

def create_table(catalog, name):
    schema = Schema(
        NestedField(field_id=1, name="sale_date", field_type=DateType(), required=False),
        NestedField(field_id=2, name="product_category", field_type=StringType(), required=False),
        NestedField(field_id=3, name="sales_amount", field_type=DoubleType(), required=False),
    )

    partition_spec = PartitionSpec(
            PartitionField(
                source_id=1,
                field_id=1000,
                transform=MonthTransform(), 
                name="sale_date_month"
                )
            )

    return catalog.create_table(
            identifier=name,
            schema=schema,
            partition_spec=partition_spec)

try:
    # テーブルを作成
    table = create_table(catalog, "sample.daily_sales")
except TableAlreadyExistsError:
    pass
