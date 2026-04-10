"""
AIテスト観点整理アシスタント - UIエントリーポイント

起動コマンド（プロジェクトルートから実行）:
    streamlit run app/streamlit_app.py
"""
import streamlit as st

from app.config import settings  # noqa: F401  設定の初期化


def main():
    st.set_page_config(
        page_title="AIテスト観点整理アシスタント",
        page_icon="🧪",
        layout="wide",
    )

    st.title("🧪 AIテスト観点整理アシスタント")
    st.caption("テスト観点の整理・生成をAIがサポートします")

    st.info("🚧 現在開発中です。詳細設計書（docs/viewpoint_generation_detailed_design.md）追加後に実装を開始します。")


if __name__ == "__main__":
    main()
