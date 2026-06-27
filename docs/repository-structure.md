# リポジトリ構造定義書 (Repository Structure Document)

## プロジェクト構造

本プロジェクトは、ローカル環境で動作する単一の Python スクリプトを中心に構成します。現時点のリポジトリにはサンプルコードが残っているため、以下はMVP実装後の目標構成です。

```
14-apple-watch-health-tracker-vs/ (リポジトリルート)
├── docs/                      # 各種仕様書・定義ドキュメント
│   ├── product-requirements.md # プロダクト要求定義書 (PRD)
│   ├── functional-design.md    # 機能設計書
│   ├── architecture.md        # 技術仕様書 (アーキテクチャ設計書)
│   ├── repository-structure.md # リポジトリ構造定義書 (本ドキュメント)
│   ├── development-guidelines.md # 開発ガイドライン
│   └── glossary.md            # 用語集
├── src/                       # Pythonソースコード
│   └── health_monthly_report.py # レポート生成スクリプト本体
├── tests/                     # pytest用テストコードディレクトリ
│   ├── test_health_monthly_report.py # スクリプト本体の機能に対するテスト
│   └── conftest.py            # pytest用共通フィクスチャ定義
├── output/                    # スクリプト実行結果の出力先 (Git管理外)
│   └── assets/                # 生成された各指標のグラフ画像 (*.png) (Git管理外)
├── export.xml                 # Apple Healthからエクスポートしたデータ (手動配置、Git管理外)
├── requirements.txt           # Python依存関係定義
├── pyproject.toml             # 任意: パッケージ化やruff/pytest設定を集約する場合に追加
├── README.md                  # セットアップ手順・実行手順の解説
├── .gitignore                 # Git除外設定ファイル
└── .python-version            # 使用するPythonバージョン定義
```

---

## ディレクトリ・ファイル詳細

### 1. ルートディレクトリ

#### `src/health_monthly_report.py`
- **役割**: レポート生成のすべての処理（XMLロード、パース、集計、グラフ画像生成、統計サマリー生成、HTMLレポート出力）を行う Python スクリプト本体。
- **実装形態**: 内部で論理的・構造的に整理された関数群（例: `parse_xml()`, `aggregate_metrics()`, `generate_charts()`, `build_stats_summary()`, `render_html()` など）で構成。

#### `export.xml` (Git管理外)
- **役割**: AppleヘルスケアAppからエクスポートされたヘルスデータ。ユーザー自身が手動でリポジトリルートに配置します。
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

- **`test_health_monthly_report.py`**:
  - `parse_xml` のストリーミング処理テスト（小さなダミーXMLを使用して検証）。
  - `aggregate_metrics` による集計および欠損値の判定テスト。
  - `build_stats_summary` の表示値生成テスト。
- **`conftest.py`**:
  - テスト用のダミーXMLデータやダミーの pandas DataFrame を生成する共通フィクスチャを記述。

---

### 4. `output/` (成果物出力ディレクトリ - Git管理外)

スクリプト実行時に自動生成されるディレクトリであり、最終成果物および中間ファイルを格納します。

- **`apple_watch_health_monthly_report_YYYY_MM.html`**: 指定した年月のHTMLレポート。
- **`assets/`**:
  - HTML内で読み込まれる、各指標の日別棒グラフ画像（`sleep_duration.png`, `steps.png` など）が保存されるサブディレクトリ。

---

## ファイル配置と命名規則

### ソースコードおよびテストファイル

| ファイル種別 | 配置先 | 命名規則 | 例 |
|------------|--------|---------|-----|
| メインスクリプト | `src/` | `snake_case.py` | `health_monthly_report.py` |
| テストコード | `tests/` | `test_[対象ファイル名].py` | `test_health_monthly_report.py` |
| テスト共通設定 | `tests/` | `conftest.py` | `conftest.py` |

### 設定ファイル

| ファイル種別 | 配置先 | 命名規則 |
|------------|--------|---------|
| 依存関係定義 | ルートディレクトリ | `requirements.txt` |
| プロジェクト設定（任意） | ルートディレクトリ | `pyproject.toml` |
| バージョン定義 | ルートディレクトリ | `.python-version` |
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
