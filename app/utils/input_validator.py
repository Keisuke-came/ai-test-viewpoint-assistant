from app.domain.models import InputData, InputValidationError


def validate_input(input_data: InputData) -> None:
    spec = input_data.spec_text.strip()
    if not spec:
        raise InputValidationError("仕様テキストを入力してください")
    if len(spec) < 20:
        raise InputValidationError("仕様テキストが短すぎます。もう少し具体的に入力してください")
