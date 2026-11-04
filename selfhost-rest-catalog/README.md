# Iceberg REST Catalogのセルフホスト

## 候補

ざっくり候補を挙げる。順序は推奨順

-   本格運用用
    -   Apache Polaris
    -   Project Nessie
    -   Apache Gravitino
-   ローカル検証用
    -   [iceberg-rest-fixture](https://github.com/apache/iceberg/tree/main/docker/iceberg-rest-fixture)
    -   PyIceberg
    -   [Boring-catalog](https://github.com/boringdata/boring-catalog)

## iceberg-rest-fixture

### ファーストタッチ

起動

```
docker run --rm -it -e CATALOG_CATALOG_NAME=mycatalog -p 8181:8181 apache/iceberg-rest-fixture
```

DuckDBからの接続

```
ATTACH 'warehouse' AS myib (TYPE iceberg, URI 'http://127.0.0.1:8181', AUTHORIZATION_TYPE 'none');
```

この時点ではネームスペース(schema)もテーブルも空っぽ。
なので自分で作っていく。

```
CREATE SCHEMA myib.foo;
USE myib.foo;
```

```
```sql
CREATE TABLE daily_sales(
    sale_date date, 
    product_category string, 
    sales_amount double)
    PARTITIONED BY (month(sale_date));
```

ここまでするとテーブルまで定義できてる。

```
$ ./_build/s3tdl.exe inspect
Warehouse:
└─ Namespaces (2):
   ├─ foo (tables: 1)
   │  ├─ Properties (1):
   │  │  └─ location: /tmp/iceberg_warehouse14475324142101227633/iceberg_data/foo
   │  └─ daily_sales
   │     ├─ Identifier: foo.daily_sales
   │     ├─ Metadata: (location: /tmp/iceberg_warehouse14475324142101227633/iceberg_data/foo/daily_sales/metadata/00000-f57c9024-f9a4-481a-af88-e87f20de062c.metadata.json)
   │     │  ├─ Version: V2
   │     │  ├─ Table UUID: ee4311b5-2953-4bf9-bced-eed8c82129bb
   │     │  ├─ Location: /tmp/iceberg_warehouse14475324142101227633/iceberg_data/foo/daily_sales
   │     │  ├─ Last Updated Millis: 1793770547740 (2026-11-04T14:35:47+09:00)
   │     │  ├─ Last Column ID: 3
   │     │  ├─ Current Schema ID: 0
   │     │  ├─ Default Partition Spec: 0
   │     │  ├─ Properties (3):
   │     │  │  ├─ created-at: 2026-11-04T05:35:47.692537400Z
   │     │  │  ├─ write.parquet.compression-codec: zstd
   │     │  │  └─ write.parquet.shred-variants: true
   │     │  └─ Last Sequence Number: 0
   │     ├─ Current Schema: (ID: 0)
   │     │  ├─ [1] sale_date: date (optional)
   │     │  ├─ [2] product_category: string (optional)
   │     │  └─ [3] sales_amount: double (optional)
   │     └─ Partition Spec: (ID: 0)
   │        └─ month_sale_date_1 (Field ID:1000) : month(sale_date)
   └─ bar (tables: 0)
      └─ Properties (1):
         └─ location: /tmp/iceberg_warehouse14475324142101227633/iceberg_data/bar
```

ただメタデータの読み込みに関して、パスの違いがあり上手く機能しないことが判明。

起動パラメーターを以下のようにすると、
DuckDBからのテーブルの作成やデータの作成に伴い、
S3上にファイルが作られる。
また参照できる。

```
docker run --rm -it \
  -e CATALOG_CATALOG_NAME=mycatalog \
  -e CATALOG_WAREHOUSE=s3://kaoriya/warehouse/ \
  -e CATALOG_IO__IMPL=org.apache.iceberg.aws.s3.S3FileIO \
  -e CATALOG_S3_ENDPOINT=https://s3.ap-northeast-1.amazonaws.com \
  -e AWS_ACCESS_KEY_ID={AWS_ACCESS_KEY_ID} \
  -e AWS_SECRET_ACCESS_KEY={AWS_SECRET_ACCESS_KEY} \
  -e AWS_REGION=ap-northeast-1 \
  -p 8181:8181 \
  apache/iceberg-rest-fixture
```

ただし iceberg-rest-fixture を再起動するとカタログ自体が失われる。

再起動を越えてカタログを保持する方法は2つある。

1.  データファイル `/tmp/iceberg_catalog.db` をボリュームに置き永続化する

    ```
    docker run --rm -it \
      -e CATALOG_CATALOG_NAME=mycatalog \
      -e CATALOG_WAREHOUSE=s3://kaoriya/warehouse/ \
      -e CATALOG_IO__IMPL=org.apache.iceberg.aws.s3.S3FileIO \
      -e CATALOG_S3_ENDPOINT=https://s3.ap-northeast-1.amazonaws.com \
      -e AWS_ACCESS_KEY_ID={AWS_ACCESS_KEY_ID} \
      -e AWS_SECRET_ACCESS_KEY={AWS_SECRET_ACCESS_KEY} \
      -e AWS_REGION=ap-northeast-1 \
      -p 8181:8181 \
      -v ./iceberg_data:/tmp \
      apache/iceberg-rest-fixture
    ```

2.  起動時に Pythonスクリプト で既存メタデータの先端として登録する

    ```
    from pyiceberg.catalog import load_catalog

    catalog = load_catalog(
        "default",
        **{
            "uri": "http://127.0.0.1:8181",
            "s3.endpoint": "https://s3.ap-northeast-1.amazonaws.com",
        }
    )

    try:
        catalog.create_namespace("foo")
    except Exception:
        pass

    catalog.register_table(
        identifier="foo.daily_sales",
        metadata_location="s3://kaoriya/warehouse/foo/daily_sales/metadata/00001-2346a8a9-ac8c-46a9-9070-e9149d006fdf.metadata.json"
    )
    ```
