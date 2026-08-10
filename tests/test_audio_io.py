from pathlib import Path

import pytest

from app.audio_io import EmptyAudioError, temp_audio_file


def test_temp_audio_file_writes_data_and_removes_it_after_use():
    data = b"some-audio-bytes"
    with temp_audio_file(data) as path:
        written = Path(path)
        assert written.exists()
        assert written.read_bytes() == data
    assert not Path(path).exists()


def test_temp_audio_file_cleans_up_even_when_body_raises():
    captured_path = None
    with pytest.raises(RuntimeError):
        with temp_audio_file(b"data") as path:
            captured_path = path
            raise RuntimeError("boom")
    assert captured_path is not None
    assert not Path(captured_path).exists()


def test_temp_audio_file_rejects_empty_bytes_with_context_in_message():
    with pytest.raises(EmptyAudioError, match="0 байт"):
        with temp_audio_file(b""):
            pass


def test_temp_audio_file_uses_fixed_suffix_not_derived_from_client_input():
    # Suffix задаётся кодом сервера, а не именем файла из запроса — клиент
    # не может повлиять на путь на диске произвольным именем загрузки.
    with temp_audio_file(b"data", suffix=".webm") as path:
        assert Path(path).suffix == ".webm"
        assert ".." not in path
