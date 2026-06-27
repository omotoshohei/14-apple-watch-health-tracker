# 開発ガイドライン (Development Guidelines)

## コーディング規約 (Python)

本プロジェクトのコードは、可読性と保守性を最大化するため、Python の標準的なコーディング規約である **PEP 8** に準拠して記述します。

### 1. 命名規則

- **変数名・関数名**: `snake_case` (小文字とアンダースコア)
  - 役割や内容が直感的に理解できる具体的な名前を付けます。
  - 例: `target_year`, `parse_health_records()`, `calculate_sleep_duration()`
- **定数名**: `UPPER_SNAKE_CASE` (大文字とアンダースコア)
  - スクリプト全体で共有される不変の値（目標値、モデル名、RecordTypeマッピングなど）。
  - 例: `METRIC_DEFINITIONS`, `DEFAULT_GEMINI_MODEL`, `GOAL_SLEEP_HOURS`
- **クラス名**: `PascalCase`
  - 将来クラスを定義する場合に使用します。
  - 例: `ReportGenerator`, `XMLStreamParser`
- **型エイリアス / 型変数**: `PascalCase`
  - 例: `DailyMetricList`

### 2. 型ヒント (Type Hints)
コードの明確化とエディタの補完機能を活用するため、関数の引数と戻り値には必ず型ヒントを記述します。

```python
# ✅ 良い例
from typing import Dict, List, Optional
import pandas as pd

def filter_data_by_month(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    # 処理
    return filtered_df
```

### 3. コメントと Docstring
- **関数ドキュメント (Docstring)**:
  すべての主要な関数には、関数の役割、引数の型と説明、戻り値の型と説明を記述します。

```python
def get_gemini_insight(metric_name: str, stats: Dict[str, float]) -> str:
    """Gemini API を使用して健康指標の英語サマリーを生成する。

    Args:
        metric_name (str): 分析対象の指標名 (例: 'Sleep Duration')
        stats (Dict[str, float]): 平均値や達成率などの統計情報

    Returns:
        str: Geminiによって生成された1〜2文の英語インサイトテキスト
    """
    # 実装
```

- **インラインコメント**:
  「何をしているか」ではなく、「なぜそうしているか」（実装の意図や特殊なロジック）を記述します。
  ```python
  # xml.etree.ElementTree.iterparse を使い、メモリ消費を抑えるために要素処理後に clear() を呼ぶ
  elem.clear()
  ```

---

## エラーハンドリング規約

1. **事前検証 (Fail-fast)**:
   - スクリプト実行開始時に、必要な環境変数 `GEMINI_API_KEY` の設定および `export.xml` ファイルの存在チェックを行い、問題があれば即座に明確なエラーメッセージを出力して処理を終了します。
2. **個別のエラーハンドリングと処理継続**:
   - 5つの指標のレポート生成において、ある1つの指標で Gemini API 呼び出しに失敗した（タイムアウトや制限等）場合、スクリプト全体を落とすのではなく、その指標のみ「サマリーコメントを代替テキスト（プレースホルダー）」に置換して処理を継続します。
3. **例外の具体的なキャッチ**:
   - `except Exception:` のような広すぎるキャッチは避け、`FileNotFoundError`, `xml.etree.ElementTree.ParseError`, `google.genai.errors.APIError`, `google.genai.errors.ClientError`, `google.genai.errors.ServerError` など、発生が想定される例外クラスを特定してキャッチします。

---

## 開発環境セットアップ

本プロジェクトでは、Python 仮想環境および依存パッケージの管理ツールとして `uv` を使用します。

### 必要なツール
- **Python**: 3.12 以上
- **uv**: 最新版

### セットアップ手順

```bash
# 1. 仮想環境の作成
uv venv

# 2. 仮想環境の有効化 (macOS / Linux)
source .venv/bin/activate

# 3. 必要な依存パッケージのインストール
uv pip install pandas matplotlib google-genai jinja2 pytest ruff
```

---

## Git 運用ルール

### 1. ブランチ戦略
- `main` ブランチは常に動作可能なリリース状態を維持します。
- 機能追加や修正を行う際は、`main` からブランチを作成して作業します。
  - `feature/[機能名]`: 新機能の実装 (例: `feature/xml-parser`)
  - `fix/[バグ内容]`: 不具合の修正 (例: `fix/missing-days-calculation`)
  - `docs/[対象]`: ドキュメントの修正 (例: `docs/guidelines-update`)

### 2. コミットメッセージ規約
コミットメッセージは、変更内容を簡潔に識別できるよう以下のプレフィックスを使用します。

- `feat`: 新機能の追加
- `fix`: バグの修正
- `docs`: ドキュメントのみの変更
- `style`: コードの動作に影響しない修正 (インデント、タイポ修正など)
- `refactor`: バグ修正や機能追加を含まないコードのリファクタリング
- `test`: テストコードの追加・修正
- `chore`: 設定ファイルやパッケージ依存関係の変更

例: `feat(api): Gemini API との連携処理を実装`

---

## テスト規約

### 1. pytest の利用
本プロジェクトのテストには `pytest` を使用します。

### 2. テスト命名規則
- テストファイル名: `tests/test_[テスト対象ファイル名].py`
- テスト関数名: `test_[関数名]_[検証内容]_[期待する結果]`
  - 例: `test_parse_xml_emptyFile_raisesValueError`

### 3. モック (Mock) の使用
- Gemini API の呼び出しなどのネットワーク通信が発生する処理や、実行環境に依存する部分は、`unittest.mock` を用いてモック化し、テスト実行時に外部通信が発生しないように設計します。

```python
# Gemini API のテスト例 (Mock使用)
from unittest.mock import MagicMock, patch
import pytest

@patch('health_monthly_report.client.models.generate_content')
def test_get_gemini_insight_success(mock_generate):
    # Mock レスポンスの設定
    mock_response = MagicMock()
    mock_response.text = "Your sleep was consistent this month."
    mock_generate.return_value = mock_response

    # テスト対象関数の呼び出しとアサーション
    insight = get_gemini_insight("Sleep", {"average": 7.5})
    assert insight == "Your sleep was consistent this month."
```
