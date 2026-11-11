# DuckDB Iceberg 拡張の調査

## 概要

Iceberg 拡張には大きく分けて2つの機能がある

1.  個別テーブルへの読取専用アクセス
2.  RESTカタログ(複数テーブル)への読書両用アクセス

いま注目しているのは、特に個別テーブルの読み取りの方。

ローカルでS3上の複数のparquetファイルを追加したメタデータを作成しS3にアップロードするだけで、
DuckDBからテーブルとして読取専用アクセスができるのではとの思い付きを検証する。

### 参考ドキュメント

-   [Iceberg拡張の概要](https://duckdb.org/docs/2.0/core_extensions/iceberg/overview)
    -   [Iceberg (RESTカタログ) への書込操作](https://duckdb.org/docs/2.0/core_extensions/iceberg/writing_to_iceberg)
    -   [Iceberg 関数](https://duckdb.org/docs/2.0/core_extensions/iceberg/iceberg_functions)
    -   [上記操作と関数のオプション一覧](https://duckdb.org/docs/2.0/core_extensions/iceberg/iceberg_options)
    -   [各カタログ種別への接続方法の説明](https://duckdb.org/docs/2.0/core_extensions/iceberg/catalogs)
    -   [トラブルシューティング](https://duckdb.org/docs/2.0/core_extensions/iceberg/troubleshooting)

## Iceberg関数

[ドキュメント: Iceberg関数](https://duckdb.org/docs/2.0/core_extensions/iceberg/iceberg_functions) より

### 関数の分類・概要

1. テーブルデータの参照・スキャン

    直接ファイルやパス、またはカタログ経由でテーブルデータやスキャン計画を取得する関数

    * `iceberg_scan(source)`: パスやメタデータファイル、S3等のオブジェクトストレージから直接Icebergテーブルを読み込む
    * `iceberg_scan_plan(table)`: スキャン時に読み込む対象となるデータファイルや削除ファイルの計画（タスク）を取得する

2. メタデータ・スナップショット・履歴の参照

    テーブルの構造、過去の変更履歴、分岐（branch/tag）などの情報を取り出す関数

    * `iceberg_metadata(source)`: マニフェストエントリ（データファイルの追加・削除状態など）を取得する
    * `iceberg_snapshots(source)`: テーブルの全スナップショット一覧（ID、タイムスタンプなど）を取得する
    * `iceberg_files(source)`: スナップショットに含まれるデータファイルおよび削除ファイルの詳細情報を取得する
    * `iceberg_manifests(source)`: スナップショットに含まれるマニフェストファイル一覧を取得する
    * `iceberg_history(source)`: カレントスナップショットに至る履歴ログ（親ID等）を取得する
    * `iceberg_refs(source)`: ブランチやタグのリファレンス情報を取得する
    * `iceberg_partition_specs(source)`: パーティション定義（Spec）の一覧を取得する

3. 統計情報の参照

    ファイル別・列別・パーティション別の各種統計データを参照する関数。

    * `iceberg_column_stats(source)`: データファイルごと・列ごとの統計情報（Min/Max、Null数など）を取得する
    * `iceberg_partition_stats(source)`: パーティションフィールドごとの統計情報を取得する

4. カログ・REST APIレスポンスの直接参照

    接続された REST Catalog から直接生のレスポンスを取得する高度な関数です。

    * `iceberg_load_table_response(table)`: REST Catalog の生データ（`LoadTable` レスポンス）を取得する
    * `iceberg_view_metadata(view)`: View の生データ（`LoadView` レスポンス）を取得する

5. プロパティの管理（テーブル / スキーマ）

    テーブルやスキーマ（ネームスペース）に付与されたメタデータプロパティの参照・更新・削除を行う関数です。

    * `iceberg_table_properties(table)`: テーブルの全プロパティを取得する
    * `set_iceberg_table_properties(table, properties)`: テーブルにプロパティを設定する
    * `remove_iceberg_table_properties(table, property_names)`: テーブルからプロパティを削除する
    * `iceberg_schema_properties(schema)`: スキーマ（ネームスペース）の全プロパティを取得する
    * `set_iceberg_schema_properties(schema, properties)`: スキーマにプロパティを設定する
    * `remove_iceberg_schema_properties(schema, property_list)`: スキーマからプロパティを削除する

6. テーブルメンテナンス・操作・変換

    ロールバック、ファイル最適化、他形式への変換、パーティション計算などを行う関数です。

    * `iceberg_rollback_to_snapshot(table, snapshot_id)`: 指定した過去のスナップショットへロールバックする
    * `iceberg_rewrite_data_files(table)`: 小さなデータファイルをまとめ（コンパクション）、最適化する
    * `iceberg_to_ducklake(iceberg_catalog, ducklake_catalog)`: Icebergのメタデータを DuckLake カタログへコピーする
    * `iceberg_bucket(num_buckets, value)`: ハッシュバケット化パーティションの変換値を計算する
    * `iceberg_truncate(width, value)`: 切り捨て（Truncate）パーティションの変換値を計算する

### 関数についての評価

「個別テーブルの読み取り」に注目する場合「1. テーブルデータの参照・スキャン」 `iceberg_scan()` を意識しておけばよい。

DuckDB だけでは複数の parquet ファイルからメタデータを生成することはできなさそう。
代わりにPyIcebergでメタデータを生成するというが最も手軽そう。

また `SET unsafe_enable_version_guessing = true;` を設定することで、
`iceberg_scan()` にディレクトリを渡すことができるようになる。
その場合、最新のメタデータを自動で判定する。
ただし、1箇所に複数のテーブルのメタデータが入ってるようなイレギュラーな状況では、自動判定に失敗すると考えられる。

## 実験

### 実験: ローカルでテーブル(メタデータ)を作ってDuckDBでアクセスする

1.  [create-table-metadata.py](create-table-metadata.py) でメタデータを作る

    データファイルは以下のS3 URLにアップロード済み:

    -   `s3://kaoriya/daily_sales/01a084a0-9551-75c0-b9f4-02c7d10fdf4e.parquet`
    -   `s3://kaoriya/daily_sales/01a084a0-9552-7780-ade6-603d6e3238ae.parquet`
    -   `s3://kaoriya/daily_sales/daily_sales-202403.parquet`

    このスクリプトのポイント:

    -   PyIcebergの役割: `InMemoryCatalog` を使い、DuckDB単体では作れないIcebergメタデータ（metadata.json / .avro）を作成し ./warehouse へ出力する。
        出力先である `warehouse` を `s3://...` に変更すると、S3へ直にメタデータを出力できる。
    -   S3パスの直指定: `table.add_files()` に `s3://` のURLを渡すことで、データファイル自体はS3に置いたままメタデータのみをローカルで生成できる。

    ```console
    $ python create-table-metadata.py
    ```

    以下のようなファイルが作られる

    ```console
    $ tree -Fh ./warehouse
    [   0]  ./warehouse/
    ├── [ 20K]  iceberg_catalog.db
    └── [   0]  log/
        └── [   0]  daily_sales/
            └── [   0]  metadata/
                ├── [ 911]  00000-25a7e6f4-7122-4c23-bbd0-9b311c1bbe54.metadata.json
                ├── [2.0K]  00001-6b0ec661-32f3-4c2e-9d25-27b4d3829f30.metadata.json
                ├── [4.8K]  9f8d3780-478e-48d9-93c0-f8f7bf4e6af4-m0.avro
                └── [1.8K]  snap-6659079514890613893-0-9f8d3780-478e-48d9-93c0-f8f7bf4e6af4.avro
    ```

    テーブル作成直後のメタデータ:

    ```console
    $ gojq . ./warehouse/log/daily_sales/metadata/00000-25a7e6f4-7122-4c23-bbd0-9b311c1bbe54.metadata.json
    {
      "current-schema-id": 0,
      "default-sort-order-id": 0,
      "default-spec-id": 0,
      "format-version": 2,
      "last-column-id": 3,
      "last-partition-id": 1000,
      "last-sequence-number": 0,
      "last-updated-ms": 1794373209085,
      "location": "D:\\home\\koron\\projects\\techdocs\\iceberg-playground\\duckdb-extension\\warehouse/log/daily_sales",
      "metadata-log": [],
      "partition-specs": [
      ... (snipped) ...
    ```

    ファイル追加後のメタデータ:

    -   `metadata-log` に1つ前のメタデータの情報が入ってる。
    -   `snapshots.[0].manifest-list` にスナップショットのマニフェストリストのAVROファイルのパスが記載されてる
    -   いずれもフルパス

    ```console
    $ gojq . ./warehouse/log/daily_sales/metadata/00001-6b0ec661-32f3-4c2e-9d25-27b4d3829f30.metadata.json
    {
      "current-schema-id": 0,
      "current-snapshot-id": 6659079514890613893,
      "default-sort-order-id": 0,
      "default-spec-id": 0,
      "format-version": 2,
      "last-column-id": 3,
      "last-partition-id": 1000,
      "last-sequence-number": 1,
      "last-updated-ms": 1794373210182,
      "location": "D:\\home\\koron\\projects\\techdocs\\iceberg-playground\\duckdb-extension\\warehouse/log/daily_sales",
      "metadata-log": [
        {
          "metadata-file": "D:\\home\\koron\\projects\\techdocs\\iceberg-playground\\duckdb-extension\\warehouse/log/daily_sales/metadata/00000-25a7e6f4-7122-4c23-bbd0-9b311c1bbe54.metadata.json",
          "timestamp-ms": 1794373209085
        }
      ],
      "partition-specs": [
      ... (snipped) ...
      "snapshots": [
        {
          "manifest-list": "D:\\home\\koron\\projects\\techdocs\\iceberg-playground\\duckdb-extension\\warehouse/log/daily_sales/metadata/snap-6659079514890613893-0-9f8d3780-478e-48d9-93c0-f8f7bf4e6af4.avro",
          "schema-id": 0,
          "sequence-number": 1,
          "snapshot-id": 6659079514890613893,
      ... (snipped) ...
    ```

    マニフェストリスト:

    -   DuckDBを使えばAVROの中がそのまま見れる
    -   `manifest_path` にマニフェストのAVROのパス

    ```console
    $ duckdb -line -c "select * from read_avro('./warehouse/log/daily_sales/metadata/snap-6659079514890613893-0-9f8d3780-478e-48d9-93c0-f8f7bf4e6af4.avro')"
           manifest_path = D:\home\koron\projects\techdocs\iceberg-playground\duckdb-extension\warehouse/log/daily_sales/metadata/9f8d3780-478e-48d9-93c0-f8f7bf4e6af4-m0.avro
         manifest_length = 4894
       partition_spec_id = 0
                 content = 0
         sequence_number = 1
     min_sequence_number = 1
       added_snapshot_id = 6659079514890613893
       added_files_count = 3
    existing_files_count = 0
     deleted_files_count = 0
        added_rows_count = 18
     existing_rows_count = 0
      deleted_rows_count = 0
              partitions = [{'contains_null': false, 'contains_nan': false, 'lower_bound': '\\x88\\x02\\x00\\x00', 'upper_bound': '\\x8A\\x02\\x00\\x00'}]
            key_metadata = NULL
    ```

    マニフェスト:

    -   `file_path` はS3を指している
    -   `partition` 情報が記録されている

        ```
        'partition': {'sale_date_month': 648}
        'partition': {'sale_date_month': 649}
        'partition': {'sale_date_month': 650}
        ```

    ```console
    $ duckdb -line -c "select * from read_avro('./warehouse/log/daily_sales/metadata/9f8d3780-478e-48d9-93c0-f8f7bf4e6af4-m0.avro')"
                  status = 1
             snapshot_id = 6659079514890613893
         sequence_number = NULL
    file_sequence_number = NULL
               data_file = {'content': 0, 'file_path': 's3://kaoriya/daily_sales/01a084a0-9551-75c0-b9f4-02c7d10fdf4e.parquet', 'file_format': PARQUET, 'partition': {'sale_date_month': 648}, 'record_count': 3, 'file_size_in_bytes': 538, 'column_sizes': {1=37, 2=56, 3=47}, 'value_counts': {1=3, 2=3, 3=3}, 'null_value_counts': {1=0, 2=0, 3=0}, 'nan_value_counts': {}, 'lower_bounds': {1='\\x19M\\x00\\x00', 2=Laptop, 3='\\x00\\x00\\x00\\x00\\x00@o@'}, 'upper_bounds': {1='\\x1AM\\x00\\x00', 2=Monitor, 3='\\x00\\x00\\x00\\x00\\x00\\x18\\x95@'}, 'key_metadata': NULL, 'split_offsets': [4], 'equality_ids': NULL, 'sort_order_id': NULL}

                  status = 1
             snapshot_id = 6659079514890613893
         sequence_number = NULL
    file_sequence_number = NULL
               data_file = {'content': 0, 'file_path': 's3://kaoriya/daily_sales/01a084a0-9552-7780-ade6-603d6e3238ae.parquet', 'file_format': PARQUET, 'partition': {'sale_date_month': 649}, 'record_count': 6, 'file_size_in_bytes': 592, 'column_sizes': {1=49, 2=81, 3=61}, 'value_counts': {1=6, 2=6, 3=6}, 'null_value_counts': {1=0, 2=0, 3=0}, 'nan_value_counts': {}, 'lower_bounds': {1='*M\\x00\\x00', 2=Keyboard, 3='\\x00\\x00\\x00\\x00\\x00\\x009@'}, 'upper_bounds': {1=',M\\x00\\x00', 2=Mouse, 3='\\x00\\x00\\x00\\x00\\x00\\xC0\\x92@'}, 'key_metadata': NULL, 'split_offsets': [4], 'equality_ids': NULL, 'sort_order_id': NULL}

                  status = 1
             snapshot_id = 6659079514890613893
         sequence_number = NULL
    file_sequence_number = NULL
               data_file = {'content': 0, 'file_path': 's3://kaoriya/daily_sales/daily_sales-202403.parquet', 'file_format': PARQUET, 'partition': {'sale_date_month': 650}, 'record_count': 9, 'file_size_in_bytes': 612, 'column_sizes': {1=47, 2=95, 3=76}, 'value_counts': {1=9, 2=9, 3=9}, 'null_value_counts': {1=0, 2=0, 3=0}, 'nan_value_counts': {}, 'lower_bounds': {1='QM\\x00\\x00', 2=Desktop, 3='\\x00\\x00\\x00\\x00\\x00\\x004@'}, 'upper_bounds': {1='TM\\x00\\x00', 2=Mouse, 3='\\x00\\x00\\x00\\x00\\x00@\\x9F@'}, 'key_metadata': NULL, 'split_offsets': [4], 'equality_ids': NULL, 'sort_order_id': NULL}
    ```

2.  DuckDB でテーブルにアクセスする

    やってることは S3 用のシークレットを登録し、`iceberg_scan()` で「ファイル追加後のメタデータ」を指定する。
    `count(*)` はメタデータだけ見れば良いので速いのに対し、
    `sum(sales_amount)` はデータファイルを見る必要があるのでちょっと時間がかかる。

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
    memory D select count(*) from iceberg_scan('./warehouse/log/daily_sales/metadata/00001-6b0ec661-32f3-4c2e-9d25-27b4d3829f30.metadata.json');
    ┌──────────────┐
    │ count_star() │
    │    int64     │
    ├──────────────┤
    │           18 │
    └──────────────┘
    memory D select sum(sales_amount) from iceberg_scan('./warehouse/log/daily_sales/metadata/00001-6b0ec661-32f3-4c2e-9d25-27b4d3829f30.metadata.json');
    ┌───────────────────┐
    │ sum(sales_amount) │
    │      double       │
    ├───────────────────┤
    │           11605.0 │
    └───────────────────┘
    ```

    また `iceberg_scan()` は、 `SET unsafe_enable_version_guessing = true;` しておけば、ディレクトリの指定でも最新のメタデータを推測して動作する。

    ```
    memory D SET unsafe_enable_version_guessing = true;
    memory D select count(*) from iceberg_scan('./warehouse/log/daily_sales');
    ┌──────────────┐
    │ count_star() │
    │    int64     │
    ├──────────────┤
    │           18 │
    └──────────────┘
    ```

3.  こうしてできたメタデータ(4ファイル)を `s3://kaoriya/daily_sales/metadata/` へアップロードする

4.  DuckDB でS3上のテーブルにアクセスする

    `iceberg_scan()` に `allow_moved_paths = true` を追加した。
    メタデータとマニフェスト内の一部のパスはローカルファイルシステム用のものだが、
    `allow_moved_paths = true` オプションが `s3://kaoriya/daily_sales` ベースに読み替えている。

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
    memory D select count(*) from iceberg_scan('s3://kaoriya/daily_sales', allow_moved_paths = true);
    ┌──────────────┐
    │ count_star() │
    │    int64     │
    ├──────────────┤
    │           18 │
    └──────────────┘
    memory D select sum(sales_amount) from iceberg_scan('s3://kaoriya/daily_sales', allow_moved_paths = true);
    ┌───────────────────┐
    │ sum(sales_amount) │
    │      double       │
    ├───────────────────┤
    │           11605.0 │
    └───────────────────┘
    ```

## まとめ

DuckDB だけでは複数 parquet から Iceberg のメタデータを生成できないが、
PyIceberg を使い、実データのあるS3上のURLを指定して `add_files()` することで、
メタデータならびにマニフェストをローカルに生成できた。

生成したメタデータとマニフェストを S3 へ配置し、DuckDB で `SET unsafe_enable_version_guessing = true;` オプションと
`iceberg_scan(..., allow_moved_paths = true)` 関数を使えば、S3上のメタデータ経由でIceberg テーブルとして読取専用アクセスが可能となる。

### 課題・未確認事項

PyIcebergによるメタデータとマニフェストの出力先はS3に変更することもできる。
その場合、`allow_moved_paths = true` は不要になるハズ。

既存テーブルに対して `add_files()` するには、今のところカタログが必要という認識でいる。
ただメタデータを読んでテーブルを構築しデータファイルを追加する、ということができるかは要検証。
