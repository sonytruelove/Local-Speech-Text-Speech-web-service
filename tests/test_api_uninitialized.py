"""До того как server.py подставит реальные модели в app.state (или пока
тестовая фикстура client их не подставила), эндпоинты должны отвечать
503, а не падать с AttributeError/None."""

from fastapi.testclient import TestClient

from app.main import app


def test_transcribe_returns_503_when_recognizer_not_wired():
    app.state.recognizer = None
    app.state.synthesizer = None
    with TestClient(app) as bare_client:
        response = bare_client.post(
            "/api/transcribe",
            files={"file": ("speech.webm", b"bytes", "audio/webm")},
        )
    assert response.status_code == 503


def test_synthesize_returns_503_when_synthesizer_not_wired():
    app.state.recognizer = None
    app.state.synthesizer = None
    with TestClient(app) as bare_client:
        response = bare_client.post("/api/synthesize", json={"text": "привет"})
    assert response.status_code == 503
