"""audio_tensor_to_wav_bytes конвертирует сэмплы Silero (float, -1..1) в WAV.
Тесты намеренно не устанавливают torch — функция принимает любой array-like
(см. её докстринг), список/кортеж достаточно для проверки контракта.
"""

import io
import wave

import pytest

from app.tts import (
    SynthesisProducedNoAudioError,
    audio_tensor_to_wav_bytes,
    synthesize_with_silero_model,
)


def test_plain_list_of_samples_produces_valid_wav():
    samples = [0.0, 0.5, -0.5, 0.25, -0.25]

    result = audio_tensor_to_wav_bytes(samples, sample_rate=16000)

    assert result[:4] == b"RIFF"
    with wave.open(io.BytesIO(result)) as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16000
        assert wav_file.getnframes() == len(samples)


def test_full_scale_sample_maps_to_near_int16_max():
    result = audio_tensor_to_wav_bytes([1.0], sample_rate=8000)

    with wave.open(io.BytesIO(result)) as wav_file:
        frame = wav_file.readframes(1)
    value = int.from_bytes(frame, byteorder="little", signed=True)
    assert value == 32767


def test_out_of_range_samples_are_clipped_not_wrapped():
    # Инвариант: выход всегда валидный int16, даже если бэкенд отдал
    # значения за пределами [-1, 1] (не должно быть overflow/wraparound).
    result = audio_tensor_to_wav_bytes([2.0, -2.0], sample_rate=8000)

    with wave.open(io.BytesIO(result)) as wav_file:
        frames = wav_file.readframes(2)
    high = int.from_bytes(frames[0:2], byteorder="little", signed=True)
    low = int.from_bytes(frames[2:4], byteorder="little", signed=True)
    assert high == 32767
    assert low == -32767


def test_sample_rate_is_passed_through_to_wav_header():
    result = audio_tensor_to_wav_bytes([0.1, 0.2, 0.3], sample_rate=48000)

    with wave.open(io.BytesIO(result)) as wav_file:
        assert wav_file.getframerate() == 48000


class _FakeAudioTensor:
    """Достаточно похоже на torch.Tensor для audio_tensor_to_wav_bytes:
    есть .numpy() и .numel()."""

    def __init__(self, values: list[float]) -> None:
        self._values = values

    def numel(self) -> int:
        return len(self._values)

    def numpy(self):
        import numpy as np

        return np.asarray(self._values, dtype="float32")


class _WorkingModel:
    def apply_tts(self, text: str, speaker: str, sample_rate: int) -> _FakeAudioTensor:
        return _FakeAudioTensor([0.1, -0.2, 0.3])


class _EmptyAudioModel:
    def apply_tts(self, text: str, speaker: str, sample_rate: int) -> _FakeAudioTensor:
        return _FakeAudioTensor([])


class _RaisingModel:
    """Как настоящий Silero на неподдерживаемом языке: голый ValueError без
    сообщения (см. регрессию, найденную в проде: EN-текст на RU-голосе)."""

    def apply_tts(self, text: str, speaker: str, sample_rate: int) -> None:
        raise ValueError


def test_synthesize_with_silero_model_returns_wav_bytes_on_success():
    result = synthesize_with_silero_model(_WorkingModel(), "текст", "speaker", 16000)
    assert result[:4] == b"RIFF"


def test_synthesize_with_silero_model_raises_on_zero_samples():
    with pytest.raises(SynthesisProducedNoAudioError):
        synthesize_with_silero_model(_EmptyAudioModel(), "текст", "speaker", 16000)


def test_synthesize_with_silero_model_wraps_backend_exception():
    # Регрессия: раньше голый ValueError из apply_tts улетал наружу
    # необработанным и ронял /api/synthesize 500-й ошибкой.
    with pytest.raises(SynthesisProducedNoAudioError):
        synthesize_with_silero_model(_RaisingModel(), "some english text", "speaker", 16000)
