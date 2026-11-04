from pyiceberg.catalog import load_catalog

catalog = load_catalog(
    "default",
    **{
        "uri": "http://127.0.0.1:8181",
        "s3.endpoint": "https://s3.ap-northeast-1.amazonaws.com",
    }
)

table = catalog.load_table('foo.daily_sales')

table.add_files(file_paths=[
    "s3://kaoriya/daily_sales/01a084a0-9551-75c0-b9f4-02c7d10fdf4e.parquet",
    "s3://kaoriya/daily_sales/01a084a0-9552-7780-ade6-603d6e3238ae.parquet",
    "s3://kaoriya/daily_sales/daily_sales-202403.parquet"
])
