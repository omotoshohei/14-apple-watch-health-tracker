# リポジトリ構造定義書 (Repository Structure Document)

## プロジェクト構造

本プロジェクトは、Apple Health XMLをローカルで解析し、月次HTMLレポートと複数月トレンドHTMLレポートを生成する Python CLI ツールです。現在はCLIエントリーポイントと共通モジュールを分離し、テストしやすい構成にしています。

```
14-apple-watch-health-tracker/ (リポジトリルート)
├── .agent/                    # Antigravity用スキル定義
├── .streamlit/                # Streamlit設定（アーカイブUI用）
├── docs/                      # 各種仕様書・定義ドキュメント
├── src/                       # Pythonソースコード
│   ├── archive/               # 過去実装・非推奨UIの保管場所
│   ├── cli/                   # CLIエントリーポイント
│   │   ├── aggregate_monthly_metrics.py
│   │   ├── aggregate_weekly_metrics.py
│   │   ├── health_monthly_report.py
│   │   ├── health_weekly_report.py
│   │   ├── health_trend_report.py
│   │   └── merge_metrics.py
│   └── health_report/         # 共通レポート生成モジュール
│       ├── __init__.py
│       ├── html.py
│       ├── preprocess.py
│       ├── report.py
│       ├── trend.py
│       └── weekly.py
├── tests/                     # pytest用テストコード
├── data/preprocess/           # 前処理済みCSV・デモ用CSV
├── output-demo/               # Git管理対象のショーケースPDF
├── input/                     # Apple Health XML配置先 (Git管理外)
├── output/                    # スクリプト実行結果 (Git管理外)
├── export.xml                 # Apple HealthエクスポートXML (Git管理外)
├── requirements.txt           # Python依存関係定義
├── pyproject.toml             # プロジェクト設定、依存関係、pytest/ruff設定
├── README.md                  # セットアップ手順・実行手順の解説
└── .gitignore                 # Git除外設定ファイル
```

---

## ディレクトリ・ファイル詳細

### 1. ルートディレクトリ

#### `src/cli/`
- **役割**: ユーザーが直接実行するCLIを配置します。
- **主なファイル**:
  - `health_monthly_report.py`: XMLまたは日別CSVから月次HTMLレポートを生成します。
  - `merge_metrics.py`: `data/preprocess/health_metrics_YYYY_MM.csv` を結合して `health_metrics_all.csv` を生成します。
  - `aggregate_monthly_metrics.py`: 日別CSVを月次集計CSVへ変換します。
  - `health_trend_report.py`: 月次集計CSVから複数月トレンドHTMLレポートを生成します。
  - `aggregate_weekly_metrics.py`: 日別CSVを週次集計CSVへ変換します。
  - `health_weekly_report.py`: 週次集計CSVから複数週トレンドHTMLレポートを生成します。

#### `src/health_report/`
- **役割**: CLIから利用される共通ロジックを配置します。
- **主なファイル**:
  - `report.py`: XMLパース、日別集計、統計計算、月次HTML生成。
  - `preprocess.py`: XMLからCSVへの前処理、日別CSVから月次CSVへの集計。
  - `trend.py`: 複数月トレンドグラフとHTML生成。
  - `weekly.py`: 月曜始まりの週次集計、週次トレンドグラフとHTML生成。
  - `html.py`: HTML内画像のData URI化など、自己完結HTML用のヘルパー。

#### `export.xml` (Git管理外)
- **役割**: AppleヘルスケアAppからエクスポートされたヘルスデータ。通常は `input/export.xml` に配置します。
- **セキュリティ**: 個人情報を含むため、Gitで追跡されないように `.gitignore` で除外します。

---

### 2. `docs/` (ドキュメントディレクトリ)

本プロジェクトの設計や規約を定義する永続ドキュメントが格納されます。

- **`product-requirements.md`**: プロダクトの目的、ペルソナ、KPI、機能要件を定義。
- **`functional-design.md`**: XMLデータのパースルール、集計ロジック、統計サマリー仕様、HTMLのUI設計を定義。
- **`architecture.md`**: テクノロジースタック、処理レイヤー、パフォーマンス目標、セキュリティを定義。
- **`repository-structure.md`**: リポジトリ構成、ファイル配置規則、Git除外設定を定義（本ドキュメント）。
- **`development-guidelines.md`**: コーディング規約、テスト方法、`uv` を用いた開発環境のセットアップ方法を定義。
- **`glossary.md`**: 各種健康指標の定義、目標値、ドメイン用語を定義。

---

### 3. `tests/` (テストディレクトリ)

スクリプトが正しく動作するかを検証するための pytest 用テストコードを格納します。

- **`test_health_monthly_report.py`**: XMLパース、日別集計、統計計算、時刻表示などの共通ロジックを検証します。
- **`test_cli.py`**: CLI引数、エラー処理、レポート生成のスモークテストを行います。
- **`test_preprocess.py`**: XMLからCSVへの前処理、日別CSVから月次CSVへの集計を検証します。
- **`test_report_csv.py`**: 既存CSV入力からの月次レポート生成を検証します。
- **`test_trend.py`**: 複数月トレンドレポート生成を検証します。
- **`test_weekly.py`**: 週次集計CSV生成と週次トレンドレポート生成を検証します。
- **`test_html.py`**: 自己完結HTML変換を検証します。

---

### 4. `data/preprocess/`

前処理済みの日別CSVと、複数月レポート用の集計CSVを格納します。

- **`health_metrics_YYYY_MM.csv`**: 対象年月の日別健康指標CSV。
- **`health_metrics_all.csv`**: 複数月の日別CSVを結合した全期間CSV。
- **`health_metrics_monthly.csv`**: トレンドレポート用の月次集計CSV。
- **`health_metrics_weekly.csv`**: 週次トレンドレポート用の週次集計CSV。

### 5. `output/` (成果物出力ディレクトリ - Git管理外)

スクリプト実行時に自動生成されるディレクトリであり、最終成果物および中間ファイルを格納します。

- **`apple_watch_health_daily_report_YYYY_MM.html`**: 指定した年月のHTMLレポート。
- **`apple_watch_health_monthly_report.html`**: 複数月トレンドHTMLレポート。
- **`apple_watch_health_weekly_report.html`**: 複数週トレンドHTMLレポート。

### 6. `output-demo/` (ショーケース - Git管理対象)

ダミーデータから生成したPDFレポートを配置します。GitHub上で生成物の見た目を確認できるようにするため、`output/` と違って Git 管理対象にします。

---

## ファイル配置と命名規則

### ソースコードおよびテストファイル

| ファイル種別 | 配置先 | 命名規則 | 例 |
|------------|--------|---------|-----|
| CLI | `src/cli/` | `snake_case.py` | `health_monthly_report.py` |
| 共通モジュール | `src/health_report/` | `snake_case.py` | `report.py` |
| テストコード | `tests/` | `test_[対象ファイル名].py` | `test_health_monthly_report.py` |
| テスト共通設定 | `tests/` | `conftest.py` | `conftest.py` |

### 設定ファイル

| ファイル種別 | 配置先 | 命名規則 |
|------------|--------|---------|
| 依存関係定義 | ルートディレクトリ | `requirements.txt` |
| プロジェクト設定 | ルートディレクトリ | `pyproject.toml` |
| Git除外定義 | ルートディレクトリ | `.gitignore` |

---

## 命名規則

### 変数・関数名 (Python)
- **変数名 / 関数名**: `snake_case` (小文字とアンダースコア)
  - 例: `target_year`, `parse_health_records()`
- **定数名**: `UPPER_SNAKE_CASE` (大文字とアンダースコア)
  - 例: `METRIC_DEFINITIONS`, `DEFAULT_MODEL`
- **クラス名 (定義する場合)**: `PascalCase`
  - 例: `ReportGenerator`

### テスト関数名 (pytest)
- **テスト関数名**: `test_[関数名]_[条件]_[期待結果]`
  - 例: `test_parse_xml_validFile_returnsRecords`, `test_aggregate_missingDays_returnsNone`

---

## 除外設定 (`.gitignore`)

個人データやローカル環境依存ファイルの流出を防ぐため、以下の除外設定を徹底します。

```text
# Python 実行時キャッシュ
__pycache__/
*.pyc

# 仮想環境
.venv/

# Apple Watch 生データ (個人情報)
export.xml
input/

# 環境変数・APIキー
.env
.env.*

# 生成物ディレクトリ
output/

# テスト・静的解析ツールキャッシュ
.pytest_cache/
.coverage
htmlcov/

# OS固有の一時ファイル
.DS_Store
```
