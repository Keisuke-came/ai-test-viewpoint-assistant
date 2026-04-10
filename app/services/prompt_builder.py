from app.domain.models import InputData

TARGET_TYPE_LABELS = {
    "screen": "画面",
    "api": "API",
    "batch": "バッチ",
    "ticket": "チケット",
    "other": "その他",
}


def build_system_prompt() -> str:
    return (
        "あなたはQA支援の専門アシスタントです。\n"
        "ユーザーが入力した仕様文・チケット文・設計メモをもとに、\n"
        "テスト観点を日本語で整理してください。\n"
        "\n"
        "必ず次のルールを守ってください。\n"
        "- 仕様に明記されていない内容を断定しない\n"
        "- 不足情報は「要確認事項」として ambiguities に出す\n"
        "- 実務でレビューしやすい粒度で出力する\n"
        "- 正常系、異常系、境界値、入力制約、業務ルール、権限、状態遷移、表示・メッセージ等を意識する\n"
        "- 出力は必ず指定されたJSON形式にする\n"
        "- 重複観点は極力避ける"
    )


def build_user_prompt(input_data: InputData) -> str:
    target_label = TARGET_TYPE_LABELS.get(input_data.target_type, input_data.target_type)
    supplemental = input_data.supplemental_text.strip() or "（なし）"
    return (
        "以下の仕様情報をもとに、テスト観点を整理してください。\n"
        "\n"
        "【対象種別】\n"
        f"{target_label}\n"
        "\n"
        "【仕様テキスト】\n"
        f"{input_data.spec_text}\n"
        "\n"
        "【補足情報】\n"
        f"{supplemental}\n"
        "\n"
        "出力要件:\n"
        "- summary: 仕様の要点を1〜3行で要約\n"
        "- viewpoints: テスト観点一覧\n"
        "  - category: 観点カテゴリ\n"
        "  - title: 観点タイトル\n"
        "  - description: 何を確認するか\n"
        "  - priority: 高 / 中 / 低\n"
        "- ambiguities: 曖昧点・要確認事項\n"
        "- notes: 注意事項\n"
        "\n"
        "必ずJSONのみを返してください。"
    )
