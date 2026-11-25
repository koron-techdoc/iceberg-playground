# AWS Athena を触ってみる

S3上のparquet形式の複数の既存ログのOLAPを作るという目的。
Iceberg REST カタログでそれらのログを束ねて、
DuckDBなどのクエリエンジンでアクセスするというのを基本方針とした。

その上で大きなクエリについては、
DuckDB等では事前に必要なリソースを割り当てておく必要があり、現実的ではない。
そこで白羽の矢を立てたのが AWS Athena 。

まずは触って、どういうものなのかを知ろうという目的。

## RESTカタログへのアクセス

AthenaがIceberg RESTカタログを含むデータソースにアクセスするには、
基本的にGlueを通す必要がある。

過去に作った S3 Tables と、アカウントのデフォルトカタログにはアクセスできた。

任意の Iceberg REST カタログを追加するには、Glueではなく、
Lake Formation の Catalog から追加する必要がある。

参考: <https://ap-northeast-1.console.aws.amazon.com/lakeformation/home?region=ap-northeast-1#catalogs>

ただし外部のRESTカタログに繋ぐには、
secret の設定など諸々の設定が必要で、
実際に接続するところまでは至っていない。

## Athena のコンソール

AWSコンソールから Athena コンソールを開くと、
いきなりクエリエディタが表示される。

実行したクエリの結果は、指定したS3バケットに出力される。

右上の小さめのナビゲーションボタンを押すと、
クエリエディタ以外のUIへのナビゲーションが現れる
ここはめちゃくちゃわかりにくい。

ノートブックエディタは、いわゆるJupyterのNotebook。

ノートブックを開くと、DPUを確保しセッションが開始する。
そのままにしておくと課金が止まらないので、
終了時には必ず Session から Terminate を選ぶこと。

(WIP)
