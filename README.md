# Iceberg Playground

## Index

Title                                                                   |Date       |Status
------------------------------------------------------------------------|-----------|-------
[RESTカタログのセルフホスト](./selfhost-rest-catalog)                   |2026-11-04 |WIP
[Glue Iceberg カタログとは](./glue-iceberg-catalog)                     |2026-10-28 |Done
[S3 TablesとDuckDBの理解](./s3tables+duckdb)                            |2026-07-08 |Done
[DuckDB拡張から見るIceberg](./duckdb-extension)                         |2026-11-11 |WIP

## Future topics

-   シングルテーブルの読み込み (DuckDB `iceberg_scan()`)
-   Apache Polaris

## Iceberg のエコシステム

Icebergのエコシステムは以下の3層に分けられる

1.  コンピュート層 (Apache Spark, AWS Athena, PyIceberg, DuckDB)
2.  カタログ層 (AWS S3 Tables, AWS Glue, Apache Polaris)
3.  ストレージ層 (S3とか)
