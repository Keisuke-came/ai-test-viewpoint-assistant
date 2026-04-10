"""
アプリ設定の読み込み。
.env ファイルから環境変数を読み込み、アプリ全体に提供する。
"""
import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")

# LLM設定（後から追加）
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
