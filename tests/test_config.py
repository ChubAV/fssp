from src.infrastructure.config import Settings, create_settings


def test_temp_path_created(tmp_path, monkeypatch):
    monkeypatch.setenv("RUCAPTCH_API_KEY", "dummy")
    monkeypatch.setenv("LOG_PATH", str(tmp_path / "logs" / "main.log"))
    monkeypatch.setenv("TEMP_PATH", str(tmp_path / "temp"))

    settings = create_settings()

    assert settings.TEMP_PATH.exists()
    assert settings.LOG_PATH.parent.exists()


def test_captcha_filled_from_root(monkeypatch):
    monkeypatch.setenv("RUCAPTCH_API_KEY", "dummy-key")

    settings = Settings()

    assert settings.captcha is not None
    assert settings.captcha.api_key == "dummy-key"
