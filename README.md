# Apple Watch Health Monthly Report

Apple WatchのヘルスケアAppからエクスポートしたデータ (`export.xml`) を解析し、16:9のアスペクト比を持つ美しい月次健康レポート（HTMLスライド形式）を自動生成するPythonツールです。

各健康指標について日別グラフと、Average / Maximum / Minimum / Goal Achieved Rate の月次統計サマリーを自動で生成・埋め込みます。

---

## 主な機能

1. **Apple Health XMLのストリーミング解析**
   - 数百MBを超える巨大な `export.xml` ファイルでも、メモリ消費を最小限に抑えながら高速にパースします。
2. **5つの健康指標の可視化と集計**
   - 以下の指標を抽出し、目標ライン（水平破線）付きの日別棒グラフを生成します：
     - **Sleep Duration**（睡眠時間、目標: 7時間）
     - **Steps**（歩数、目標: 8,000歩）
     - **Active Energy Burned**（活動カロリー、目標: 500 kcal）
     - **Exercise Time**（エクササイズ時間、目標: 30分）
     - **Stand Hours**（スタンド時間、目標: 12時間）
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
│   ├── cli/                   # CLI実行用コード
│   │   └── health_monthly_report.py
│   ├── streamlit_app/         # Streamlit Web UI実行用コード
│   │   └── app.py
│   └── health_report/         # 共通レポート生成モジュール
│       ├── __init__.py
│       ├── report.py          # 解析・グラフ生成・統計サマリー生成ロジック
│       └── html.py            # 自己完結HTML変換ヘルパー
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

### 4. レポート生成の実行 (Web UI版)

Streamlitを用いたWeb UIから直感的にレポートの生成・閲覧・ダウンロードが可能です。

```bash
# Web UIの起動
.venv/bin/streamlit run src/streamlit_app/app.py
```

- **ファイルのアップロード**: 画面上のファイルアップローダーに `export.xml` をドラッグ＆ドロップまたはファイル選択してアップロードします。
- **ファイルサイズ上限**: デフォルトで `.streamlit/config.toml` にて最大 **1024MB (1GB)** までアップロードできるように設定されています。さらに大きいデータをアップロードする場合は、`server.maxUploadSize` の値を変更してください。
- **ダウンロード**: 生成成功後、「Download Self-Contained Report HTML」ボタンから画像が埋め込まれた自己完結型HTMLをダウンロードできます。

### 5. レポート生成の実行 (CLI版)

対象の年・月を指定してスクリプトを実行します。外部APIキーは不要です。

```bash
# 例: 2026年6月のレポートを生成する場合
uv run python src/cli/health_monthly_report.py --year 2026 --month 6 --xml input/export.xml --output-dir output
```

実行が完了すると、`output/` ディレクトリに以下のファイルが生成されます：
- **レポートHTML**: `output/apple_watch_health_monthly_report_2026_06.html` (グラフはインラインSVGとして埋め込まれ、このファイル単体で完結します)

### 6. ショーケース（デモ出力）の確認

ポートフォリオのデモンストレーション用として、ダミーデータから事前に生成したレポートHTMLが同梱されています。
- **デモレポート**: [output-demo/apple_watch_health_monthly_report_2026_06.html](file:///Users/sho/code/01-project/14-apple-watch-health-tracker/output-demo/apple_watch_health_monthly_report_2026_06.html)

このファイルをブラウザでダブルクリックするだけで、グラフ描画やダークモードなどの表示スタイル、16:9スライドによるレスポンシブなスライド閲覧動作を今すぐ確認することができます。

---

## Antigravityスキル

月次レポート生成の手順は、Antigravity用スキルとしても定義しています。

- **CLI版**: `.agent/skills/monthly-report-cli/SKILL.md`
  - `input/*.xml` から対象XMLを選択し、`uv run python src/cli/health_monthly_report.py ...` で `output/` にHTMLを生成します。
- **Streamlit版**: `.agent/skills/monthly-report-streamlit/SKILL.md`
  - Streamlit Web UIを起動し、ブラウザからXMLをアップロードして自己完結HTMLをプレビュー・ダウンロードします。

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
