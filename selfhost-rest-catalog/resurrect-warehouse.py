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
