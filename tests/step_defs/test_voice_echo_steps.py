"""Step-definitions для tests/features/voice_echo.feature (Stage 1 спека)."""

from __future__ import annotations

from pytest_bdd import given, scenarios, then, when

from tests.helpers import make_wav_bytes

scenarios("../features/voice_echo.feature")


# --- Сценарий: успешный проход "сказал -> услышал" ---------------------


@given('пользователь нажал "Старт" и наговорил фразу в микрофон', target_fixture="recorded_audio")
def user_recorded_a_phrase(fake_recognizer):
    fake_recognizer.text = "привет, как дела"
    fake_recognizer.language = "ru"
    return make_wav_bytes(duration_ms=800)


@when('пользователь нажимает "Стоп"', target_fixture="transcribe_response")
def user_stops_recording(client, recorded_audio):
    return client.post(
        "/api/transcribe",
        files={"file": ("speech.webm", recorded_audio, "audio/webm")},
    )


@then("сервис возвращает распознанный текст этой фразы")
def transcript_matches_spoken_phrase(transcribe_response, fake_recognizer):
    assert transcribe_response.status_code == 200
    assert transcribe_response.json()["text"] == fake_recognizer.text


@then("сервис возвращает аудио (audio/wav) с озвучкой того же текста")
def transcript_gets_synthesized_back(client, transcribe_response, fake_synthesizer):
    text = transcribe_response.json()["text"]
    response = client.post("/api/synthesize", json={"text": text})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content
    assert fake_synthesizer.calls == [text]


# --- Сценарий: тишина не озвучивается -----------------------------------


@given("пользователь записал только тишину", target_fixture="recorded_audio")
def user_recorded_silence(fake_recognizer):
    fake_recognizer.text = ""
    fake_recognizer.language = "ru"
    return make_wav_bytes(duration_ms=500)


@when("запись отправлена на распознавание", target_fixture="transcribe_response")
def recording_is_sent_for_transcription(client, recorded_audio):
    return client.post(
        "/api/transcribe",
        files={"file": ("speech.webm", recorded_audio, "audio/webm")},
    )


@then("распознанный текст пуст")
def transcript_is_empty(transcribe_response):
    assert transcribe_response.json()["text"] == ""


@then("синтез речи не вызывается для пустого текста")
def synthesizer_was_never_called(fake_synthesizer):
    assert fake_synthesizer.calls == []


# --- Сценарий: пустой текст отклоняется на синтезе ----------------------


@when(
    "клиент напрямую отправляет пустой текст в /api/synthesize",
    target_fixture="synthesize_response",
)
def client_sends_empty_text_to_synthesize(client):
    return client.post("/api/synthesize", json={"text": ""})


@then("сервис отвечает ошибкой 400, аудио не генерируется")
def synthesize_is_rejected(synthesize_response, fake_synthesizer):
    assert synthesize_response.status_code == 400
    assert fake_synthesizer.calls == []
