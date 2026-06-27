# 2026-06-27: Apple Health export.xml が大きすぎて Cloud Run inline function で扱えない

## 結論

Google Cloud Run inline editor 版は断念する。

Apple Health の標準エクスポートは全期間の `export.xml` を出力する仕様で、対象月だけを Health アプリ上で選んで出力できない。そのため実データでは XML が大きくなりやすく、Cloud Run の HTTP request size limit に当たる。

実際に Cloud Run へ `export.xml` をアップロードしたところ、以下のエラーが表示された。

```text
Error: Request Entity Too Large
Your client issued a request that was too large.
```

## 発生した問題

- Cloud Run inline function 自体のデプロイは成功した。
- ただし、レポート生成時に大きな `export.xml` をフォームから直接アップロードすると失敗した。
- `MAX_UPLOAD_BYTES` をアプリ側で増やしても、Cloud Run の手前の HTTP request size limit を超えるため解決できない。
- Apple Health アプリ標準のエクスポートでは対象月だけの XML を直接作れない。

## 原因

今回の構成は、ブラウザから Cloud Run function へ `multipart/form-data` で `export.xml` を直接送信する設計だった。

この方式では、Cloud Run がリクエスト本文を受け取る段階でサイズ制限に当たる。アプリケーションコードの `MAX_UPLOAD_BYTES` チェックや `/tmp` 保存処理に到達する前に拒否される可能性がある。

## 判断

Cloud Run inline editor 版は、Apple Health の実データを扱う本番/実用構成としては不適切と判断する。

理由:

- Apple Health の `export.xml` は全期間データになり、実データでは大きくなりやすい。
- inline function への直接アップロードは大容量ファイルに向かない。
- レポート生成は XML 解析、グラフ生成、Gemini API 呼び出しを含み、単一 HTTP request 内で完結させるには重い。
- 対象月だけに絞った XML を事前作成すれば動く可能性はあるが、ユーザー体験として自然ではない。

## 代替案

### 採用しない案

- Cloud Run inline editor へ `export.xml` を直接アップロードする方式
- `MAX_UPLOAD_BYTES` だけを増やす方式
- Health アプリから対象月だけを直接 export する前提の方式

### 現実的な案

- ローカル Streamlit アプリで全量 `export.xml` を処理する。
- ローカルで対象月だけにフィルタした XML を作る補助スクリプトを用意する。
- 将来クラウド化する場合は、Cloud Run に直接アップロードせず Cloud Storage を使う。
  - ブラウザまたはローカルツールから Cloud Storage へアップロードする。
  - Cloud Run / Cloud Run Jobs は Cloud Storage 上の object を読み込んで処理する。
  - 必要に応じて非同期ジョブ、進捗表示、完了通知を設計する。

## 今後の方針

このフェーズでは Cloud Run inline editor 版の継続実装は停止する。

優先する方向:

1. ローカル実行版の体験を整える。
2. 必要であれば、対象月だけに絞った軽量 XML を生成するローカルスクリプトを追加する。
3. クラウド対応を再開する場合は、Cloud Storage 前提の別設計として扱う。
