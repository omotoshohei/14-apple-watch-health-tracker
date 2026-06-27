# Apple Watch Health Monthly Report

Apple WatchのヘルスケアAppからエクスポートしたデータ (`export.xml`) を解析し、16:9のアスペクト比を持つ美しい月次健康レポート（HTMLスライド形式）を自動生成するPythonツールです。

各健康指標の統計データに基づき、Gemini API (`gemini-3.5-flash`) を使用して英語のパーソナライズされたインサイトサマリーも自動で生成・埋め込みます。

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
4. **Gemini APIによる自動英語インサイト**
   - 月内の傾向、目標値の達成状況、翌月に向けた改善ポイントを、Gemini APIを用いて1〜2文の簡潔な英語サマリーとして生成します。
5. **16:9 HTMLスライドレポートの出力**
   - ブラウザで快適に閲覧・プレゼンテーションできる 1920x1080px (16:9) サイズのスライドが縦に並んだ単一の HTML ファイルを出力します。
   - ダークモードに対応したスタイリッシュなデザイン、ウィンドウサイズに応じた自動スケーリング、キーボードでのスライド移動をサポートしています。

---

## 技術スタック

- **言語**: Python 3.12+
- **環境・パッケージ管理**: `uv`
- **データ解析・可視化**: `pandas`, `matplotlib`
- **LLM API**: `google-genai` (Jinja2テンプレートによるHTML生成)
- **テスト・品質管理**: `pytest`, `ruff`

---

## ディレクトリ構造

```text
.
├── docs/                      # プロジェクト仕様書・各種定義ドキュメント
│   ├── product-requirements.md # プロダクト要求定義書 (PRD)
│   ├── functional-design.md    # 機能設計書
│   ├── architecture.md        # 技術仕様書 (アーキテクチャ設計書)
│   ├── repository-structure.md # リポジトリ構造定義書
│   ├── development-guidelines.md # 開発ガイドライン
│   └── glossary.md            # 用語集
├── src/                       # Pythonソースコード
│   ├── health_monthly_report.py # レポート生成スクリプト本体
│   └── example.py             # 動作確認用サンプルスクリプト
├── tests/                     # テストコードディレクトリ
│   ├── test_health_monthly_report.py
│   └── conftest.py
├── output/                    # スクリプト実行結果の出力先 (Git管理外)
│   └── assets/                # 生成されたグラフ画像 (*.png) (Git管理外)
├── export.xml                 # Apple Healthからエクスポートしたデータ (Git管理外)
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
3. エクスポートされた ZIP ファイルを展開し、中にある `export.xml` を本プロジェクトのルートディレクトリに配置します。

### 3. サンプルデータによる動作確認 (オプション)

実データがない場合、テスト用のサンプルデータを生成して動作確認が可能です。以下のコマンドで 2026年6月 のダミーデータを生成します：

```bash
uv run python create_sample_data.py
```

### 4. レポート生成の実行

`GEMINI_API_KEY` を環境変数に設定し、対象の年・月を指定してスクリプトを実行します。

```bash
# 例: 2026年6月のレポートを生成する場合
GEMINI_API_KEY="YOUR_GEMINI_API_KEY" uv run python src/health_monthly_report.py --year 2026 --month 6
```

実行が完了すると、`output/` ディレクトリに以下のファイルが生成されます：
- **レポートHTML**: `output/apple_watch_health_monthly_report_2026_06.html`
- **グラフ画像**: `output/assets/` 配下に各指標のPNG画像

### 5. レポートの閲覧

生成された `output/apple_watch_health_monthly_report_YYYY_MM.html` をブラウザで直接開きます。
- **スライド移動**: 左右の矢印キー、Spaceキー、またはPageUp/PageDownキーで前後のスライドへ滑らかに切り替わります。
- **自動スケーリング**: 16:9比率を維持したまま、ウィンドウサイズに合わせて画面全体がフィットします。

---

## テストとコード品質

### テストの実行

```bash
# pytestによるテスト実行
uv run pytest
```

### コード品質チェック (Linter/Formatter)

```bash
# 静的解析 (Ruff Linter)
uv run ruff check src/

# 自動フォーマット (Ruff Formatter)
uv run ruff format src/
```
