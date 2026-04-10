"""
アプリ設定の読み込み。
.env ファイルから環境変数を読み込み、アプリ全体に提供する。
"""
import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))


def validate_settings() -> None:
    if not OPENAI_API_KEY:
        raise EnvironmentError(
            "OPENAI_API_KEY が設定されていません。.env ファイルを確認してください。"
        )
