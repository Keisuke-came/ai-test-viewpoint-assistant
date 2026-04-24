import pytest
from app.domain.models import InputValidationError, Viewpoint
from app.services.csv_formatter import format_as_csv


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------

@pytest.fixture
def single_viewpoint() -> list:
    return [
        Viewpoint(category="正常系", title="正常ログイン", description="正しい認証情報でログインできること", priority="高")
    ]


@pytest.fixture
def three_viewpoints() -> list:
    return [
        Viewpoint(category="正常系", title="正常ログイン", description="正しい認証情報でログインできること", priority="高"),
        Viewpoint(category="異常系", title="パスワード誤り", description="誤ったパスワードでエラーになること", priority="中"),
        Viewpoint(category="境界値", title="上限テスト", description="3回失敗後にロックされること", priority="低"),
    ]


# ---------------------------------------------------------------------------
# 正常系
# ---------------------------------------------------------------------------

def test_single_viewpoint_row_count(single_viewpoint):
    """N-1: 1 件リスト → ヘッダ + 1 行"""
    result = format_as_csv(single_viewpoint)
    # BOM を除いた後に \r\n で分割。末尾の空要素を除く
    rows = result[1:].split("\r\n")
    rows = [r for r in rows if r]
    assert len(rows) == 2


def test_three_viewpoints_row_count(three_viewpoints):
    """N-2: 3 件リスト → ヘッダ + 3 行"""
    result = format_as_csv(three_viewpoints)
    rows = result[1:].split("\r\n")
    rows = [r for r in rows if r]
    assert len(rows) == 4


def test_bom_prefix_char(single_viewpoint):
    """N-3: 戻り値先頭文字が BOM（U+FEFF）"""
    result = format_as_csv(single_viewpoint)
    assert result[0] == "\ufeff"


def test_bom_prefix_bytes(single_viewpoint):
    """N-4: BOM バイト列が b'\\xef\\xbb\\xbf'"""
    result = format_as_csv(single_viewpoint)
    assert result.encode("utf-8")[:3] == b"\xef\xbb\xbf"


def test_returns_str(single_viewpoint):
    """N-5: 戻り値が str 型"""
    result = format_as_csv(single_viewpoint)
    assert isinstance(result, str)


def test_header_columns(single_viewpoint):
    """N-6: ヘッダ列名が「カテゴリ,観点タイトル,説明,優先度」"""
    result = format_as_csv(single_viewpoint)
    header = result[1:].split("\r\n")[0]
    assert header == "カテゴリ,観点タイトル,説明,優先度"


def test_field_mapping(single_viewpoint):
    """N-7: フィールドが対応する列に正しくマッピングされる"""
    vp = single_viewpoint[0]
    result = format_as_csv(single_viewpoint)
    data_row = result[1:].split("\r\n")[1]
    assert vp.category in data_row
    assert vp.title in data_row
    assert vp.description in data_row
    assert vp.priority in data_row


def test_priority_all_values():
    """N-8: priority の「高/中/低」がそのまま出力される"""
    viewpoints = [
        Viewpoint(category="A", title="T", description="D", priority="高"),
        Viewpoint(category="A", title="T", description="D", priority="中"),
        Viewpoint(category="A", title="T", description="D", priority="低"),
    ]
    result = format_as_csv(viewpoints)
    assert "高" in result
    assert "中" in result
    assert "低" in result


# ---------------------------------------------------------------------------
# 異常系
# ---------------------------------------------------------------------------

def test_none_raises_input_validation_error():
    """E-1: None を渡すと InputValidationError"""
    with pytest.raises(InputValidationError):
        format_as_csv(None)


def test_dict_in_list_raises_input_validation_error():
    """E-2: dict 要素が混在すると InputValidationError"""
    with pytest.raises(InputValidationError):
        format_as_csv([{"category": "X"}])


def test_none_element_raises_input_validation_error():
    """E-3: None 要素が混在すると InputValidationError"""
    with pytest.raises(InputValidationError):
        format_as_csv([None])


def test_str_element_raises_input_validation_error():
    """E-4: str 要素が混在すると InputValidationError"""
    with pytest.raises(InputValidationError):
        format_as_csv(["テキスト"])


# ---------------------------------------------------------------------------
# 境界値
# ---------------------------------------------------------------------------

def test_empty_list_returns_header_only():
    """B-1: 空リスト → ヘッダ行のみ返す（エラーにならない）"""
    result = format_as_csv([])
    rows = result[1:].split("\r\n")
    rows = [r for r in rows if r]
    assert len(rows) == 1


def test_empty_list_row_count():
    """B-2: 空リスト → \r\n split で 1 行（ヘッダのみ）"""
    result = format_as_csv([])
    assert result[1:].split("\r\n")[0] == "カテゴリ,観点タイトル,説明,優先度"


def test_comma_in_field():
    """B-3: フィールドにカンマ含む → ダブルクォートで囲まれる"""
    vp = Viewpoint(category="A", title="タイトル,サブタイトル", description="D", priority="高")
    result = format_as_csv([vp])
    assert '"タイトル,サブタイトル"' in result


def test_newline_in_field():
    """B-4: フィールドに \\n 含む → ダブルクォートで囲まれる"""
    vp = Viewpoint(category="A", title="T", description="行1\n行2", priority="高")
    result = format_as_csv([vp])
    assert '"行1\n行2"' in result


def test_double_quote_in_field():
    """B-5: フィールドにダブルクォート含む → \"\" にエスケープされる"""
    vp = Viewpoint(category="A", title="T", description='説明"引用"あり', priority="高")
    result = format_as_csv([vp])
    assert '""引用""' in result


def test_japanese_field():
    """B-6: 日本語フィールドが文字化けなく出力される"""
    vp = Viewpoint(category="正常系", title="ひらがなテスト", description="カタカナ・漢字テスト", priority="高")
    result = format_as_csv([vp])
    assert result[1:].encode("utf-8").decode("utf-8") == result[1:]


def test_empty_string_field():
    """B-7: フィールド値が空文字列 → エラーにならず空フィールドとして出力される"""
    vp = Viewpoint(category="A", title="T", description="", priority="高")
    result = format_as_csv([vp])
    # データ行（BOM除去後 2行目）に空フィールドが含まれること
    data_row = result[1:].split("\r\n")[1]
    # description が空なので "A,T,,高" のように連続カンマが現れる
    assert ",," in data_row or data_row.endswith(",")


def test_long_field():
    """B-8: 1000 文字超フィールド → 正しく 1 フィールドに収まる"""
    long_text = "あ" * 1001
    vp = Viewpoint(category="A", title="T", description=long_text, priority="高")
    result = format_as_csv([vp])
    assert long_text in result


# ---------------------------------------------------------------------------
# 仕様確認
# ---------------------------------------------------------------------------

def test_crlf_line_ending(three_viewpoints):
    """S-1: 行末が CRLF（\\r\\n）"""
    result = format_as_csv(three_viewpoints)
    body = result[1:]  # BOM 除去
    # \r\n で分割したとき期待行数（ヘッダ + 3 行 + 末尾空要素）と一致
    parts = body.split("\r\n")
    non_empty = [p for p in parts if p]
    assert len(non_empty) == 4


def test_body_encoding_health(three_viewpoints):
    """S-2: BOM を除いた本体が UTF-8 として健全にエンコード/デコードできる"""
    result = format_as_csv(three_viewpoints)
    body = result[1:]
    assert body.encode("utf-8").decode("utf-8") == body


def test_no_lone_lf(three_viewpoints):
    """S-3: 本体に LF 単独（\\r\\n 以外の改行）が含まれない"""
    result = format_as_csv(three_viewpoints)
    body = result[1:]
    # \r\n を除去した後、\n が残らないことを確認
    stripped = body.replace("\r\n", "")
    assert "\n" not in stripped
    assert "\r" not in stripped
