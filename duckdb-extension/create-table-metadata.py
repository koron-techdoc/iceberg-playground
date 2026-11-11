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

# スキーマの定義:
# 実際のparquetファイルから取るように作ることもできるが、
# ここではは愚直に書き下している。
schema = Schema(
    NestedField(field_id=1, name="sale_date", field_type=DateType(), required=False),
    NestedField(field_id=2, name="product_category", field_type=StringType(), required=False),
    NestedField(field_id=3, name="sales_amount", field_type=DoubleType(), required=False),
)

# パーティションの定義:
# parquetファイルからは作れないので、手動で構築する必要がある。
# `CREATE TABLE ... (...);` をAIに渡して、PyIceberg用のコードを生成して
# と依頼すると簡単にできる。
partition_spec = PartitionSpec(
    PartitionField(
        source_id=1,
        field_id=1000,
        transform=MonthTransform(), 
        name="sale_date_month"
    )
)

# インメモリカタログとして新規に作成する。
# 既存のカタログ・テーブルからから作るには要修正なのだが、
# ファイルベースでのカタログでは立ちいかなくなる可能性が高い。
catalog = InMemoryCatalog(
    name="default",
    warehouse=os.path.abspath("./warehouse"),
)

try:
    catalog.create_namespace("log")
except NamespaceAlreadyExistsError:
    pass

try:
    # テーブルを作成
    table = catalog.create_table(
            identifier="log.daily_sales",
            schema=schema,
            partition_spec=partition_spec,
            )

    # テーブルにファイルを登録
    table.add_files(file_paths=[
        "s3://kaoriya/daily_sales/01a084a0-9551-75c0-b9f4-02c7d10fdf4e.parquet",
        "s3://kaoriya/daily_sales/01a084a0-9552-7780-ade6-603d6e3238ae.parquet",
        "s3://kaoriya/daily_sales/daily_sales-202403.parquet"
        ])
except TableAlreadyExistsError:
    pass
