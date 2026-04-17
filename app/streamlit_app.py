"""
AIテスト観点整理アシスタント - UIエントリーポイント

起動コマンド（プロジェクトルートから実行）:
    streamlit run app/streamlit_app.py
"""
import logging
import streamlit as st

from app.domain.models import (
    InputData,
    DisplayResult,
    InputValidationError,
    LlmApiError,
    ResponseFormatError,
    ApplicationError,
)
from app.services.viewpoint_generation_service import ViewpointGenerationService

logger = logging.getLogger(__name__)

TARGET_TYPE_OPTIONS = {
    "画面": "screen",
    "API": "api",
    "バッチ": "batch",
    "チケット": "ticket",
    "その他": "other",
}

ERROR_MESSAGES = {
    InputValidationError: "入力内容を見直してください",
    LlmApiError: "AI呼び出しに失敗しました。時間をおいて再試行してください",
    ResponseFormatError: "AI応答形式が不正です。再試行してください",
    ApplicationError: "システムエラーが発生しました",
}


def _init_session_state() -> None:
    defaults = {
        "display_result": None,
        "error_message": None,
        "status_message": None,
        "clear_trigger": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def handle_generate(target_type: str, spec_text: str, supplemental_text: str) -> None:
    st.session_state.error_message = None
    st.session_state.status_message = None
    st.session_state.display_result = None

    try:
        input_data = InputData(
            target_type=target_type,
            spec_text=spec_text,
            supplemental_text=supplemental_text,
        )
        service = ViewpointGenerationService()
        result: DisplayResult = service.generate(input_data)
        st.session_state.display_result = result
        st.session_state.status_message = "観点の生成が完了しました"
    except InputValidationError as e:
        st.session_state.error_message = f"{ERROR_MESSAGES[InputValidationError]}: {e}"
    except LlmApiError:
        st.session_state.error_message = ERROR_MESSAGES[LlmApiError]
    except ResponseFormatError:
        st.session_state.error_message = ERROR_MESSAGES[ResponseFormatError]
    except EnvironmentError as e:
        st.session_state.error_message = str(e)
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        st.session_state.error_message = ERROR_MESSAGES[ApplicationError]


def handle_clear() -> None:
    st.session_state.display_result = None
    st.session_state.error_message = None
    st.session_state.status_message = None
    st.session_state.clear_trigger += 1


def render_input_form() -> tuple[str, str, str]:
    st.subheader("入力")

    label_options = list(TARGET_TYPE_OPTIONS.keys())
    selected_label = st.selectbox("対象種別", options=label_options, key="target_label")
    target_type = TARGET_TYPE_OPTIONS[selected_label]

    spec_text = st.text_area(
        "仕様テキスト *",
        height=200,
        placeholder="テスト対象の仕様を入力してください（20文字以上）",
        key=f"spec_text_{st.session_state.clear_trigger}",
    )

    supplemental_text = st.text_area(
        "補足情報（任意）",
        height=100,
        placeholder="前提条件・背景など補足があれば入力してください",
        key=f"supplemental_text_{st.session_state.clear_trigger}",
    )

    return target_type, spec_text, supplemental_text


def render_result(result: DisplayResult) -> None:
    st.divider()
    st.subheader("生成結果")

    st.markdown("### サマリ")
    st.info(result.summary)

    st.markdown("### テスト観点")
    for category, viewpoints in result.grouped_viewpoints.items():
        with st.expander(f"**{category}** （{len(viewpoints)}件）", expanded=True):
            for vp in viewpoints:
                priority_color = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(vp.priority, "⚪")
                st.markdown(f"**{priority_color} [{vp.priority}] {vp.title}**")
                st.caption(vp.description)

    if result.ambiguities:
        st.markdown("### 曖昧点・確認事項")
        for item in result.ambiguities:
            st.warning(item, icon="❓")

    if result.notes:
        st.markdown("### 注意事項")
        for item in result.notes:
            st.info(item, icon="ℹ️")

    st.divider()
    st.markdown("### Markdownコピー用")
    st.text_area(
        "以下をコピーしてご利用ください",
        value=result.markdown_text,
        height=300,
        key="markdown_output",
    )


def render_eval_section() -> None:
    """評価機能セクションを描画する。"""
    st.divider()
    with st.expander("🔬 AI 出力品質 評価（ルールベース）", expanded=False):
        st.caption("事前定義ケースを一括実行し、生成結果をルールベースで評価します。LLM の追加呼び出しは行いません。")

        col1, col2 = st.columns([1, 5])
        with col1:
            run_clicked = st.button("評価を実行", key="eval_run")
        with col2:
            refresh = st.checkbox("キャッシュ無視（再生成）", value=False, key="eval_refresh")

        if run_clicked:
            try:
                from app.eval.case_loader import load_cases
                from app.eval.reporter import to_markdown
                from app.eval.runner import run_cases

                cases = load_cases()
                with st.spinner(f"{len(cases)} ケースを評価中..."):
                    report = run_cases(cases, refresh=refresh)

                pass_rate = (
                    f"{report.passed / report.total * 100:.1f}%" if report.total > 0 else "N/A"
                )
                if report.failed == 0:
                    st.success(f"全 {report.total} ケース PASS ({pass_rate})")
                else:
                    st.warning(f"{report.passed}/{report.total} PASS ({pass_rate})  — {report.failed} FAIL")

                rows = []
                for r in report.results:
                    rows.append({
                        "case_id": r.case_id,
                        "タイトル": r.title,
                        "判定": "✅ PASS" if r.passed else "❌ FAIL",
                        "観点数": r.viewpoint_count,
                        "キャッシュ": "hit" if r.cache_hit else "miss",
                        "時間(s)": r.duration_seconds,
                        "失敗理由": "; ".join(r.failures) if r.failures else "-",
                    })
                st.dataframe(rows, use_container_width=True)

                with st.expander("Markdown レポート"):
                    st.text_area(
                        "コピー用",
                        value=to_markdown(report),
                        height=300,
                        key="eval_md_output",
                    )

            except EnvironmentError as e:
                st.error(str(e))
            except Exception as e:
                logger.error("評価実行エラー: %s", e)
                st.error(f"評価実行中にエラーが発生しました: {e}")


def render_page() -> None:
    st.set_page_config(
        page_title="AIテスト観点整理アシスタント",
        page_icon="🧪",
        layout="wide",
    )
    st.title("🧪 AIテスト観点整理アシスタント")
    st.caption("テスト観点の整理・生成をAIがサポートします")

    _init_session_state()

    target_type, spec_text, supplemental_text = render_input_form()

    col1, col2 = st.columns([1, 5])
    with col1:
        generate_clicked = st.button("観点を生成する", type="primary")
    with col2:
        clear_clicked = st.button("クリア")

    if generate_clicked:
        with st.spinner("AIが観点を生成中です..."):
            handle_generate(target_type, spec_text, supplemental_text)

    if clear_clicked:
        handle_clear()
        st.rerun()

    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    if st.session_state.status_message:
        st.success(st.session_state.status_message)

    if st.session_state.display_result:
        render_result(st.session_state.display_result)

    render_eval_section()


if __name__ == "__main__":
    render_page()
