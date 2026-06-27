# 実装ガイド (Implementation Guide)

## Python 規約

### 型定義

**型ヒントの使用**:
```python
# ✅ 良い例: 型ヒントを明示
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# ❌ 悪い例: 型ヒントなし
def process_items(items):
    return {item: len(item) for item in items}
```

**Optional と Union**:
```python
from typing import Optional

# ✅ 良い例
def find_user(user_id: str) -> Optional[dict]:
    ...

# Python 3.10+ では | を使用可能
def find_user(user_id: str) -> dict | None:
    ...
```

### 命名規則

**変数・関数**:
```python
# 変数: snake_case、名詞
user_name = "John"
task_list = []
is_completed = True

# 関数: snake_case、動詞で始める
def fetch_user_data(): ...
def validate_email(email: str): ...
def calculate_total_price(items: list): ...

# Boolean: is_, has_, should_, can_ で始める
is_valid = True
has_permission = False
should_retry = True
can_delete = False
```

**クラス**:
```python
# クラス: PascalCase、名詞
class TaskManager: ...
class UserAuthenticationService: ...
```

**定数**:
```python
# UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
API_BASE_URL = "https://api.example.com"
DEFAULT_TIMEOUT = 5000
```

**ファイル名**:
```python
# モジュール・ユーティリティ: snake_case
# task_service.py
# user_repository.py
# format_date.py

# テストファイル: test_ プレフィックス
# test_task_service.py
# test_user_repository.py
```

### 関数設計

**単一責務の原則**:
```python
# ✅ 良い例: 単一の責務
def calculate_total_price(items: list[dict]) -> float:
    return sum(item["price"] * item["quantity"] for item in items)

def format_price(amount: float) -> str:
    return f"¥{amount:,.0f}"

# ❌ 悪い例: 複数の責務
def calculate_and_format_price(items: list[dict]) -> str:
    total = sum(item["price"] * item["quantity"] for item in items)
    return f"¥{total:,.0f}"
```

**関数の長さ**:
- 目標: 20行以内
- 推奨: 50行以内
- 100行以上: リファクタリングを検討

### エラーハンドリング

**カスタム例外クラス**:
```python
class ValidationError(Exception):
    def __init__(self, message: str, field: str, value):
        super().__init__(message)
        self.field = field
        self.value = value

class NotFoundError(Exception):
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} not found: {id}")
        self.resource = resource
        self.id = id
```

**エラーハンドリングパターン**:
```python
# ✅ 良い例: 適切なエラーハンドリング
def get_task(task_id: str) -> dict:
    task = repository.find_by_id(task_id)
    if task is None:
        raise NotFoundError("Task", task_id)
    return task

# ❌ 悪い例: エラーを無視
def get_task(task_id: str) -> dict | None:
    try:
        return repository.find_by_id(task_id)
    except Exception:
        return None  # エラー情報が失われる
```

**エラーメッセージ**:
```python
# ✅ 良い例: 具体的で解決策を示す
raise ValidationError(
    f"タイトルは1-200文字で入力してください。現在の文字数: {len(title)}",
    field="title",
    value=title,
)

# ❌ 悪い例: 曖昧で役に立たない
raise ValueError("Invalid input")
```

## コメント規約

### ドキュメントコメント

**docstring形式**:
```python
def create_task(title: str, description: str = "") -> dict:
    """タスクを作成する。

    Args:
        title: タスクのタイトル（1〜200文字）
        description: タスクの説明（省略可）

    Returns:
        作成されたタスクの辞書

    Raises:
        ValidationError: titleが空または200文字超の場合
    """
    ...
```

### インラインコメント

```python
# ✅ 理由を説明
# キャッシュを無効化して最新データを取得
cache.clear()

# ✅ TODO・FIXMEを活用
# TODO: キャッシュ機能を実装 (Issue #123)
# FIXME: 大量データでパフォーマンス劣化 (Issue #456)

# ❌ コードの内容を繰り返すだけ
# iを1増やす
i += 1
```

## セキュリティ

### 入力検証

```python
# ✅ 良い例: 厳密な検証
import re

def validate_email(email: str) -> None:
    if not email or not isinstance(email, str):
        raise ValidationError("メールアドレスは必須です", "email", email)

    pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    if not re.match(pattern, email):
        raise ValidationError("メールアドレスの形式が不正です", "email", email)

    if len(email) > 254:
        raise ValidationError("メールアドレスが長すぎます", "email", email)
```

### 機密情報の管理

```python
# ✅ 良い例: 環境変数から読み込み
import os

api_key = os.environ.get("API_KEY")
if not api_key:
    raise EnvironmentError("API_KEY環境変数が設定されていません")

# ❌ 悪い例: ハードコード
api_key = "sk-1234567890abcdef"  # 絶対にしない！
```

## テストコード

### テストの構造 (Given-When-Then)

```python
import pytest

class TestTaskService:
    def test_正常なデータでタスクを作成できる(self):
        # Given: 準備
        service = TaskService(mock_repository)
        task_data = {"title": "テストタスク", "description": "テスト用の説明"}

        # When: 実行
        result = service.create(task_data)

        # Then: 検証
        assert result["id"] is not None
        assert result["title"] == "テストタスク"

    def test_タイトルが空の場合ValidationErrorをスローする(self):
        # Given: 準備
        service = TaskService(mock_repository)
        invalid_data = {"title": ""}

        # When/Then: 実行と検証
        with pytest.raises(ValidationError):
            service.create(invalid_data)
```

### フィクスチャの使用

```python
import pytest

@pytest.fixture
def mock_repository():
    # テスト用リポジトリのセットアップ
    return MockRepository()

@pytest.fixture
def task_service(mock_repository):
    return TaskService(mock_repository)
```

## チェックリスト

実装完了前に確認:

### コード品質
- [ ] 命名が明確で一貫している（snake_case）
- [ ] 関数が単一の責務を持っている
- [ ] マジックナンバーがない
- [ ] 型ヒントが適切に記載されている
- [ ] エラーハンドリングが実装されている

### セキュリティ
- [ ] 入力検証が実装されている
- [ ] 機密情報がハードコードされていない
- [ ] SQLインジェクション対策がされている

### パフォーマンス
- [ ] 適切なデータ構造を使用している
- [ ] 不要な計算を避けている

### テスト
- [ ] pytestでテストが書かれている
- [ ] テストがパスする（`pytest src/`）
- [ ] エッジケースがカバーされている

### ドキュメント
- [ ] 関数・クラスにdocstringがある
- [ ] 複雑なロジックにコメントがある
- [ ] TODOやFIXMEが記載されている（該当する場合）

### ツール
- [ ] ruffのLintエラーがない（`ruff check src/`）
- [ ] ruffのフォーマットが統一されている（`ruff format --check src/`）
