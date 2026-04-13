import pytest
from app.domain.models import InputData, Viewpoint, LlmResult


@pytest.fixture
def valid_input_data() -> InputData:
    return InputData(
        target_type="screen",
        spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
        supplemental_text="ログイン失敗時は最大3回まで試行可能",
    )


@pytest.fixture
def sample_viewpoint() -> Viewpoint:
    return Viewpoint(
        category="正常系",
        title="正常ログイン",
        description="正しいメールアドレスとパスワードを入力した場合にログインできること",
        priority="高",
    )


@pytest.fixture
def sample_llm_result() -> LlmResult:
    return LlmResult(
        summary="ログイン機能のテスト観点。正常系・異常系・境界値を含む。",
        viewpoints=[
            Viewpoint(
                category="正常系",
                title="正常ログイン",
                description="正しい認証情報でログインできること",
                priority="高",
            ),
            Viewpoint(
                category="異常系",
                title="パスワード誤り",
                description="誤ったパスワードを入力した場合にエラーになること",
                priority="高",
            ),
            Viewpoint(
                category="境界値",
                title="ログイン試行回数上限",
                description="3回失敗後にアカウントがロックされること",
                priority="中",
            ),
            Viewpoint(
                category="正常系",
                title="補足情報あり正常ログイン",
                description="補足情報の条件下でも正常にログインできること",
                priority="低",
            ),
        ],
        ambiguities=["ロック解除の手順が仕様に記載されていない"],
        notes=["テスト環境ではロック解除APIが別途必要"],
    )
