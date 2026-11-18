# カタログ無しのテーブル

カタログ無しでテーブルだけを更新する試み。
失敗した。

## 構成

-   [`01-create_table.py`](./01-create_table.py)

    `InMemoryCatalog` でテーブルを作り、2つのファイルを `add_files` する。

-   [`02-add_files.py`](./02-add_files.py)

    `InMemoryCatalog` で1を作ったwarehouseを指定し、
    `load_table` でロードしたテーブルへ
    追加で1つのファイルの `add_files` を試みる。

    結果はNoSuchTableErrorで失敗。
    名前からテーブル本体を知るためのカタログが無いのだから当然。

-   [`03-static-table.py`](./03-static-table.py)

    1で作られたテーブルのメタデータJSONを指定して `StaticTable` を作る。
    そのテーブルに対して `add_files` を試みる。

    結果は `NotImplementedError` で失敗。
    [ドキュメント](https://py.iceberg.apache.org/api/#static-table) に以下のように記載されており、
    その通りになっている。

    > The static-table does not allow for write operations.

    エラー全文は以下のとおり。カタログが無いのだから書けないという理屈。

    ```
    Traceback (most recent call last):
      File "D:\home\koron\projects\techdocs\iceberg-playground\duckdb-extension\03-static-table.py", line 10, in <module>
        table.add_files(file_paths=[
        ~~~~~~~~~~~~~~~^^^^^^^^^^^^^
            "s3://kaoriya/daily_sales/daily_sales-202403.parquet"
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            ])
            ^^
      File "D:\home\koron\projects\techdocs\iceberg-playground\venv\Lib\site-packages\pyiceberg\table\__init__.py", line 1815, in add_files
        with self.transaction() as tx:
             ~~~~~~~~~~~~~~~~^^
      File "D:\home\koron\projects\techdocs\iceberg-playground\venv\Lib\site-packages\pyiceberg\table\__init__.py", line 270, in __exit__
        self.commit_transaction()
        ~~~~~~~~~~~~~~~~~~~~~~~^^
      File "D:\home\koron\projects\techdocs\iceberg-playground\venv\Lib\site-packages\pyiceberg\table\__init__.py", line 1125, in commit_transaction
        self._table._do_commit(  # pylint: disable=W0212
        ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
            updates=self._updates,
            ^^^^^^^^^^^^^^^^^^^^^^
            requirements=self._requirements,
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        )
        ^
      File "D:\home\koron\projects\techdocs\iceberg-playground\venv\Lib\site-packages\pyiceberg\table\__init__.py", line 1840, in _do_commit
        response = self.catalog.commit_table(self, requirements, updates)
      File "D:\home\koron\projects\techdocs\iceberg-playground\venv\Lib\site-packages\pyiceberg\catalog\noop.py", line 116, in commit_table
        raise NotImplementedError
    NotImplementedError
    ```
