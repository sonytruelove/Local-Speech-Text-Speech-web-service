from app.stt import join_segments


class _Seg:
    def __init__(self, text: str) -> None:
        self.text = text


def test_join_segments_concatenates_segment_texts_in_order():
    segments = [_Seg("привет"), _Seg(" мир")]
    assert join_segments(segments) == "привет мир"


def test_join_segments_empty_iterable_returns_empty_string():
    assert join_segments([]) == ""


def test_join_segments_result_never_has_leading_or_trailing_whitespace():
    # Инвариант, а не пересказ реализации: чем бы ни была окружена речь
    # по краям, результат должен быть обрезан.
    segments = [_Seg("   текст с пробелами по краям   ")]
    result = join_segments(segments)
    assert result == result.strip()
    assert result == "текст с пробелами по краям"
