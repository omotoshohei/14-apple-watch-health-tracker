# Apple Watch Health Monthly Report

Apple WatchのヘルスケアAppからエクスポートしたデータ (`export.xml`) を解析し、16:9のアスペクト比を持つ美しい月次健康レポート（HTMLスライド形式）を自動生成するPythonツールです。

各健康指標について日別グラフと、Average / Maximum / Minimum / Goal Achieved Rate の月次統計サマリーを自動で生成・埋め込みます。

---

## 主な機能

1. **Apple Health XMLのストリーミング解析**
   - 数百MBを超える巨大な `export.xml` ファイルでも、メモリ消費を最小限に抑えながら高速にパースします。
2. **11の健康指標の可視化と集計**
   - 以下の指標を抽出し、目標ライン（水平破線）付きの日別棒グラフを生成します：
     - **Sleep Duration**（睡眠時間、目標: 6.5時間）
     - **Steps**（歩数、目標: 15,000歩）
     - **Active Energy Burned**（活動カロリー、目標: 500 kcal）
     - **Exercise Time**（エクササイズ時間、目標: 30分）
     - **Stand Hours**（スタンド時間、目標: 12時間）
     - **Sleep Onset Time**（就寝時間、目標: 翌 01:30 (25.5)）
     - **Wake Time**（起床時間、目標: 翌 08:30 (32.5)）
     - **Awake Count**（途中覚醒回数、目標: 1回）
     - **Awake Duration**（途中覚醒時間、目標: 5分）
     - **Longest Awake Duration**（最長途中覚醒時間、目標: 5分）
     - **First Morning Awake Time**（朝の最初の覚醒時間、目標: 翌 07:00 (31.0)）
3. **欠損値の適切なハンドリング**
   - 未装着日などのデータ欠損を正しく識別し、統計（平均値など）に影響を与えないように除外して計算します。
4. **決定的な月次統計サマリー**
   - 欠損日を除外して Average、Maximum、Minimum、Goal Achieved Rate を計算し、各指標スライドに表示します。
5. **16:9 HTMLスライドレポートの出力**
   - ブラウザで快適に閲覧・プレゼンテーションできる 1920x1080px (16:9) サイズのスライドが縦に並んだ単一の HTML ファイルを出力します。
   - ダークモードに対応したスタイリッシュなデザイン、ウィンドウサイズに応じた自動スケーリング、キーボードでのスライド移動をサポートしています。
6. **月次トレンドレポート（複数月の長期推移）**
   - 複数月の月次集計データ (`health_metrics_monthly.csv`) を元に、各指標の長期トレンドを示す折れ線グラフ（目標値ライン付き）と、月別の詳細数値を表すテーブルを並列配置したHTMLスライドレポートを自動生成します。
   - レポートは洗練されたダークテーマデザインを採用しています。
7. **週次トレンドレポート（複数週の短期推移）**
   - 結合済み日別CSV (`health_metrics_all.csv`) から月曜始まりの完全週だけを集計した `health_metrics_weekly.csv` を生成します。
   - 週次平均の折れ線グラフ、目標ライン、週別テーブルを指標ごとのHTMLスライドとして出力します。

---

## 技術スタック

- **言語**: Python 3.12+
- **環境・パッケージ管理**: `uv`
- **Web UI フレームワーク**: `streamlit`
- **データ解析・可視化**: `pandas`, `matplotlib`
- **HTML生成**: `jinja2`
- **テスト・品質管理**: `pytest`, `ruff`

---

## ディレクトリ構造

```text
.
├── .agent/                    # Antigravity用スキル定義
│   └── skills/
│       ├── monthly-report-cli/       # CLI版月次レポート生成スキル
│       └── monthly-report-streamlit/ # Streamlit版月次レポート生成スキル
├── .streamlit/                # Streamlit設定ディレクトリ
│   └── config.toml            # ファイルアップロード上限等の設定
├── docs/                      # プロジェクト仕様書・各種定義ドキュメント
│   ├── product-requirements.md # プロダクト要求定義書 (PRD)
│   ├── functional-design.md    # 機能設計書
│   ├── architecture.md        # 技術仕様書 (アーキテクチャ設計書)
│   ├── repository-structure.md # リポジトリ構造定義書
│   ├── development-guidelines.md # 開発ガイドライン
│   └── glossary.md            # 用語集
├── src/                       # Pythonソースコード
│   ├── archive/               # アーカイブされた未使用のモジュール
│   │   ├── google-cloud-run-function-inline/
│   │   └── streamlit_app/
│   ├── cli/                   # CLI実行用コード
│   │   ├── aggregate_monthly_metrics.py # 日別CSVから月次集計CSVを生成
│   │   ├── aggregate_weekly_metrics.py  # 日別CSVから週次集計CSVを生成
│   │   ├── health_monthly_report.py     # 月次HTMLレポート生成
│   │   ├── health_weekly_report.py      # 週次トレンドHTMLレポート生成
│   │   ├── health_trend_report.py       # 複数月トレンドHTMLレポート生成
│   │   └── merge_metrics.py             # 月別CSVを全期間CSVへ結合
│   └── health_report/         # 共通レポート生成モジュール
│       ├── __init__.py
│       ├── html.py            # 自己完結HTML変換ヘルパー
│       ├── preprocess.py      # XMLからCSVへの前処理モジュール
│       ├── report.py          # 月次レポート生成ロジック
│       ├── trend.py           # 複数月トレンドレポート生成ロジック
│       └── weekly.py          # 週次集計・週次トレンドレポート生成ロジック
├── tests/                     # テストコードディレクトリ
│   ├── test_cli.py            # CLIのスモークテスト
│   ├── test_health_monthly_report.py # 共通モジュールのテスト
│   ├── test_html.py           # 自己完結HTML変換のテスト
│   ├── test_preprocess.py     # XML前処理・月次集計のテスト
│   ├── test_report_csv.py     # CSV入力レポート生成のテスト
│   ├── test_trend.py          # トレンドレポートのテスト
│   └── conftest.py
├── output/                    # スクリプト実行結果の出力先 (Git管理外)
├── output-demo/               # ポートフォリオショーケース用のデモPDFレポート (Git管理対象)
├── input/                     # Apple HealthからエクスポートしたXMLの配置先 (Git管理外)
├── requirements.txt           # Python依存パッケージ定義
├── pyproject.toml             # プロジェクト設定 (ruff/pytestなど)
└── README.md                  # 本ドキュメント
```

---

## セットアップと使用方法

### 1. 開発環境の構築

本プロジェクトではパッケージ管理に `uv` の使用を推奨しています。

```bash
# 仮想環境の作成
uv venv

# 仮想環境の有効化 (macOS / Linux)
source .venv/bin/activate

# 依存関係のインストール
uv pip install -r requirements.txt
```

### 2. Apple Watchデータの配置

1. iPhoneの「ヘルスケア」Appを開きます。
2. 右上のユーザーアイコンをタップし、「すべてのヘルスケアデータを書き出す」を選択します。
3. エクスポートされた ZIP ファイルを展開し、中にある `export.xml` を `input/` ディレクトリに配置します。
   *(※ Streamlit UI版を使用する場合は、起動後にブラウザから直接アップロードすることも可能です)*

### 3. サンプルデータによる動作確認 (オプション)

実データがない場合、テスト用のサンプルデータを生成して動作確認が可能です。以下のコマンドで 2026年6月 のダミーデータを生成します：

```bash
# uv を使用する場合
uv run python create_sample_data.py

# または標準の Python
python create_sample_data.py
```

### 4. レポート生成の実行 (Web UI版 - アーカイブ済み)

※ Web UI (Streamlit) 機能は現在非推奨となり、`src/archive/` に移動されました。現在は CLI 版のみをサポート・推奨しています。

### 5. レポート生成の実行 (CLI版)

対象の年・月を指定し、データ入力元を選択して実行します。本ツールは、XMLから中間CSVを生成する「前処理」と、CSVからHTMLを生成する「レポート生成」の2つのステップで構成されます。

#### A. XMLから一括でレポート生成を行う場合 (デフォルト)
```bash
# 例: 2026年6月のXMLからCSVを抽出し、それをもとにHTMLレポートを生成する
uv run python src/cli/health_monthly_report.py --year 2026 --month 6 --xml input/export.xml --output-dir output
```
実行が完了すると、中間CSV (`data/preprocess/health_metrics_2026_06.csv`) と HTMLレポート (`output/apple_watch_health_daily_report_2026_06.html`) の両方が出力されます。

#### B. 既存のCSVデータからHTMLレポートのみを再生成する場合
XMLの巨大なパース処理をスキップし、すでに抽出済みのCSVを使用して高速にHTMLを再生成できます。
```bash
# 例: 既存のCSVを指定してHTMLレポートのみを出力する
uv run python src/cli/health_monthly_report.py --year 2026 --month 6 --csv data/preprocess/health_metrics_2026_06.csv --output-dir output
```

#### C. XMLからCSVデータのみを生成する場合 (前処理のみ)
HTMLレポートを生成せず、データ抽出 (CSV出力) のみを行いたい場合に指定します。
```bash
# 例: CSV抽出のみを実行する
uv run python src/cli/health_monthly_report.py --year 2026 --month 6 --xml input/export.xml --preprocess-only --csv-output output/my_metrics_2026_06.csv
```

### 6. ショーケース（デモ出力）の確認

ポートフォリオのデモンストレーション用として、ダミーデータから事前に生成したレポートPDFが同梱されています。
- **日次デモレポート**: [output-demo/apple_watch_health_daily_report_2026_05.pdf](output-demo/apple_watch_health_daily_report_2026_05.pdf)
- **週次デモレポート**: [output-demo/apple_watch_health_weekly_report.pdf](output-demo/apple_watch_health_weekly_report.pdf)
- **月次デモレポート**: [output-demo/apple_watch_health_monthly_report.pdf](output-demo/apple_watch_health_monthly_report.pdf)

このファイルをPDFビューアまたはブラウザで開くことで、グラフ描画やダークモードなどの表示スタイル、16:9スライド形式の見た目を今すぐ確認することができます。

### 7. トレンドレポートの実行（複数月の長期推移）

複数月にわたる健康データのトレンド（月ごとの平均推移）を示す HTML レポートを生成します。

```bash
# 1. 各月のCSVファイルをすべて結合して health_metrics_all.csv を作成
uv run python src/cli/merge_metrics.py

# 2. 結合CSVから月次集計データ health_metrics_monthly.csv を算出
uv run python src/cli/aggregate_monthly_metrics.py

# 3. トレンドレポートHTMLを生成
uv run python src/cli/health_trend_report.py
```
生成されたレポートは `output/apple_watch_health_monthly_report.html` に出力されます。

### 8. 週次トレンドレポートの実行（複数週の短期推移）

結合済みの日別CSVから、月曜始まりの完全週だけを対象にした週次集計CSVとHTMLレポートを生成します。

```bash
# 1. 各月のCSVファイルをすべて結合して health_metrics_all.csv を作成
uv run python src/cli/merge_metrics.py

# 2. 結合CSVから週次集計データ health_metrics_weekly.csv を算出
uv run python src/cli/aggregate_weekly_metrics.py

# 3. 週次トレンドレポートHTMLを生成
uv run python src/cli/health_weekly_report.py
```
生成された集計CSVは `data/preprocess/health_metrics_weekly.csv`、レポートは `output/apple_watch_health_weekly_report.html` に出力されます。

### 9. HTMLレポートをPDFへ変換

生成済みのHTMLレポートを、横長16:9のPDFへ変換できます。デフォルトでは `output/*.html` を対象にし、同名PDFを `output/pdf/` に出力します。

```bash
uv run python src/cli/html_to_pdf.py
```

単一HTMLだけを変換する場合:

```bash
uv run python src/cli/html_to_pdf.py --input output/apple_watch_health_weekly_report.html
```

入力・出力ディレクトリを明示する場合:

```bash
uv run python src/cli/html_to_pdf.py --input-dir output --output-dir output/pdf
```

既存PDFを上書きしたくない場合は `--skip-existing` を指定します。

```bash
uv run python src/cli/html_to_pdf.py --skip-existing
```

初回実行時に Chromium が未導入のエラーが出た場合は、以下を実行してください。

```bash
uv run playwright install chromium
```

---

## Antigravityスキル

月次レポート生成の手順は、Antigravity用スキルとしても定義しています。

- **CLI版**: `.agent/skills/monthly-report-cli/SKILL.md`
  - 前処理済みCSV、または `input/*.xml` から `uv run python src/cli/health_monthly_report.py ...` でHTMLを生成します。
- **前処理版**: `.agent/skills/preprocess/SKILL.md`
  - Apple Health XMLから対象月の11指標を抽出し、日別CSVを生成します。
- **トレンドレポート版**: `.agent/skills/monthly-trend-report/SKILL.md`
  - `health_metrics_all.csv` から月次集計データを作成し、健康指標の長期トレンドを示すHTMLレポートを生成します。
- **マージ版**: `.agent/skills/merge-metrics/SKILL.md`
  - 各月の健康指標データCSVをマージし、全期間のデータを含む `health_metrics_all.csv` を生成・更新します。

---

## テストとコード品質

### テストの実行

```bash
# pytestによるテスト実行
uv run python -m pytest
```

### コード品質チェック (Linter/Formatter)

```bash
# 静的解析 (Ruff Linter)
uv run python -m ruff check src/

# フォーマット確認 (Ruff Formatter)
uv run python -m ruff format --check src/

# 自動フォーマット
uv run python -m ruff format src/
```
