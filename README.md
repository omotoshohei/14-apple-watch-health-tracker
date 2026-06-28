# Apple Watch Health Monthly Report

Apple WatchのヘルスケアAppからエクスポートしたデータ (`export.xml`) を解析し、16:9のアスペクト比を持つ美しい月次健康レポート（HTMLスライド形式）を自動生成するPythonツールです。

各健康指標について日別グラフと、Average / Maximum / Minimum / Goal Achieved Rate の月次統計サマリーを自動で生成・埋め込みます。

---

## 主な機能

1. **Apple Health XMLのストリーミング解析**
   - 数百MBを超える巨大な `export.xml` ファイルでも、メモリ消費を最小限に抑えながら高速にパースします。
2. **11の健康指標の可視化と集計**
   - 以下の指標を抽出し、目標ライン（水平破線）付きの日別棒グラフを生成します：
     - **Sleep Duration**（睡眠時間、目標: 7時間）
     - **Steps**（歩数、目標: 8,000歩）
     - **Active Energy Burned**（活動カロリー、目標: 500 kcal）
     - **Exercise Time**（エクササイズ時間、目標: 30分）
     - **Stand Hours**（スタンド時間、目標: 12時間）
     - **Sleep Onset Time**（就寝時間、目標: 深夜 0:00 (24.0)）
     - **Wake Time**（起床時間、目標: 翌 07:00 (31.0)）
     - **Awake Count**（途中覚醒回数、目標: 0回）
     - **Awake Duration**（途中覚醒時間、目標: 0分）
     - **Longest Awake Duration**（最長途中覚醒時間、目標: 0分）
     - **First Morning Awake Time**（朝の最初の覚醒時間、目標: 翌 06:00 (30.0)）
3. **欠損値の適切なハンドリング**
   - 未装着日などのデータ欠損を正しく識別し、統計（平均値など）に影響を与えないように除外して計算します。
4. **決定的な月次統計サマリー**
   - 欠損日を除外して Average、Maximum、Minimum、Goal Achieved Rate を計算し、各指標スライドに表示します。
5. **16:9 HTMLスライドレポートの出力**
   - ブラウザで快適に閲覧・プレゼンテーションできる 1920x1080px (16:9) サイズのスライドが縦に並んだ単一の HTML ファイルを出力します。
   - ダークモードに対応したスタイリッシュなデザイン、ウィンドウサイズに応じた自動スケーリング、キーボードでのスライド移動をサポートしています。

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
│   │   └── health_monthly_report.py
│   └── health_report/         # 共通レポート生成モジュール
│       ├── __init__.py
│       ├── html.py            # 自己完結HTML変換ヘルパー
│       ├── preprocess.py      # XMLからCSVへの前処理モジュール
│       └── report.py          # 解析・グラフ生成・統計サマリー生成ロジック
├── tests/                     # テストコードディレクトリ
│   ├── test_cli.py            # CLIのスモークテスト
│   ├── test_health_monthly_report.py # 共通モジュールのテスト
│   ├── test_html.py           # 自己完結HTML変換のテスト
│   └── conftest.py
├── output/                    # スクリプト実行結果の出力先 (Git管理外)
├── output-demo/               # ポートフォリオショーケース用のデモHTMLレポート (Git管理対象)
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
実行が完了すると、中間CSV (`data/preprocess/health_metrics_2026_06.csv`) と HTMLレポート (`output/apple_watch_health_monthly_report_2026_06.html`) の両方が出力されます。

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

ポートフォリオのデモンストレーション用として、ダミーデータから事前に生成したレポートHTMLが同梱されています。
- **デモレポート**: [output-demo/apple_watch_health_monthly_report_2026_05.html](output-demo/apple_watch_health_monthly_report_2026_05.html)

このファイルをブラウザでダブルクリックするだけで、グラフ描画やダークモードなどの表示スタイル、16:9スライドによるレスポンシブなスライド閲覧動作を今すぐ確認することができます。

---

## Antigravityスキル

月次レポート生成の手順は、Antigravity用スキルとしても定義しています。

- **CLI版**: `.agent/skills/monthly-report-cli/SKILL.md`
  - 前処理済みCSV、または `input/*.xml` から `uv run python src/cli/health_monthly_report.py ...` でHTMLを生成します。
- **前処理版**: `.agent/skills/preprocess/SKILL.md`
  - Apple Health XMLから対象月の6指標を抽出し、日別CSVを生成します。

---

## テストとコード品質

### テストの実行

```bash
# pytestによるテスト実行
.venv/bin/pytest
```

### コード品質チェック (Linter/Formatter)

```bash
# 静的解析 (Ruff Linter)
.venv/bin/ruff check src/

# 自動フォーマット (Ruff Formatter)
.venv/bin/ruff format src/
```
