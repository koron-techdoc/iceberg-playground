# `allow_moved_paths = true` 無しでアクセス

DuckDBから `allow_moved_paths = true` を指定せずに済むように、
PyIceberg でメタデータを直接 S3 へ出力する試み。
成功した。


## 構成

-   [`01-create_table.py`](./01-create_table.py)

    ローカルファイルベースのカタログを作り、
    テーブルを作成する。
    `warehouse` はS3を直接指定。

-   [`02-add_two_files.py`](./02-add_two_files.py)

    ファイルを2つ `add_files` する。

-   [`03-add_another_file.py`](./03-add_another_file.py)

    ファイルを1つ `add_files` する。

その後、DuckDBからアクセスできることを確認。
この場合でも `SET unsafe_enable_version_guessing = true;` は必須。

```console
$ duckdb
DuckDB v2.0.0 (Cyanoptera)
Enter ".help" for usage hints.
memory D create secret (type s3, provider credential_chain);
┌─────────┐
│ Success │
│ boolean │
├─────────┤
│ true    │
└─────────┘
memory D SET unsafe_enable_version_guessing = true;
memory D select count(*) from iceberg_scan('s3://kaoriya/warehouse/s3-direct/sample/daily_sales');
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│           18 │
└──────────────┘
memory D select sum(sales_amount) from iceberg_scan('s3://kaoriya/warehouse/s3-direct/sample/daily_sales');
┌───────────────────┐
│ sum(sales_amount) │
│      double       │
├───────────────────┤
│           11605.0 │
└───────────────────┘
```


カタログ情報はローカル(上記Pythonスクリプトを実行したPC)の
`iceberg_catalog.db` (SQLiteのファイル) に入ってる。

そのスキーマと、各テーブルの内容は以下の通り:

```console
$ sqlite3 ./iceberg_catalog.db
SQLite version 3.54.1 2026-10-16 14:45:20
Enter ".help" for usage hints.
SQLite-3.54 iceberg_catalog.db-> .schema
CREATE TABLE iceberg_tables (
        catalog_name VARCHAR(255) NOT NULL,
        table_namespace VARCHAR(255) NOT NULL,
        table_name VARCHAR(255) NOT NULL,
        metadata_location VARCHAR(1000),
        previous_metadata_location VARCHAR(1000),
        iceberg_type VARCHAR(5),
        PRIMARY KEY (catalog_name, table_namespace, table_name)
);
CREATE TABLE iceberg_namespace_properties (
        catalog_name VARCHAR(255) NOT NULL,
        namespace VARCHAR(255) NOT NULL,
        property_key VARCHAR(255) NOT NULL,
        property_value VARCHAR(1000) NOT NULL,
        PRIMARY KEY (catalog_name, namespace, property_key)
);
SQLite-3.54 iceberg_catalog.db-> select * from iceberg_namespace_properties ;
╭──────────────┬───────────┬──────────────┬────────────────╮
│ catalog_name │ namespace │ property_key │ property_value │
╞══════════════╪═══════════╪══════════════╪════════════════╡
│ default      │ sample    │ exists       │ true           │
╰──────────────┴───────────┴──────────────┴────────────────╯
SQLite-3.54 iceberg_catalog.db-> select * from iceberg_tables;
╭────────────┬───────────────┬───────────┬──────────────────────────────┬─────────────────────────────────────────────────┬────────────╮
│catalog_name│table_namespace│table_name │      metadata_location       │              previous_metadata...               │iceberg_type│
╞════════════╪═══════════════╪═══════════╪══════════════════════════════╪═════════════════════════════════════════════════╪════════════╡
│default     │sample         │daily_sales│s3://kaoriya/warehouse/s3-    │s3://kaoriya/warehouse/s3-direct/sample/         │TABLE       │
│            │               │           │direct/sample/daily_sales/    │daily_sales/metadata/00001-4d4f875d-eef8-41bc-   │            │
│            │               │           │metadata/00002-b046181e-dc5a- │96e5-1ed249804a80.metadata.json                  │            │
│            │               │           │4d0a-9b31-834ab092a40c.       │                                                 │            │
│            │               │           │metadata.json                 │                                                 │            │
╰────────────┴───────────────┴───────────┴──────────────────────────────┴─────────────────────────────────────────────────┴────────────╯
```

極めてシンプル。必要最小限のものという感じ。

このファイル(ステート)を保持しておけば、テーブルへのparquetファイルの追加は手軽にできる。

メタデータからこのステートを再構築すれば、PyIcebergとしてはステートレスでできそう。
