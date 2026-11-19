import pytest
import requests
import api
from api import search_videos, YouTubeAPIError


class FakeResponse:
    """Підробна відповідь сервера: має лише те, чим користується наш код."""

    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data
        self.text = str(data)

    def json(self):
        return self._data


@pytest.fixture(autouse=True)
def fake_key(monkeypatch):
    """autouse=True: виконується перед КОЖНИМ тестом цього файлу автоматично.
    Підставляємо тестовий ключ, щоб тести не залежали від твого .env."""
    monkeypatch.setattr(api, "API_KEY", "test-key")


def test_returns_items_on_success(monkeypatch):
    items = [{"id": {"videoId": "v1"}}]
    monkeypatch.setattr(api.requests, "get", lambda *args, **kwargs: FakeResponse(200, {"items": items}))
    # lambda — коротка функція в один рядок: хоч би з чим її викликали, вона повертає FakeResponse

    assert search_videos("docker") == items


def test_sends_query_and_key_as_parameters(monkeypatch):
    captured = {}                                   # сюди «підглянемо», з чим нас викликали

    def fake_get(url, params, timeout):
        captured["params"] = params
        return FakeResponse(200, {"items": []})

    monkeypatch.setattr(api.requests, "get", fake_get)
    search_videos("python tutorial")

    assert captured["params"]["q"] == "python tutorial"   # параметр пошуку дійшов до запиту
    assert captured["params"]["key"] == "test-key"


def test_empty_result_returns_empty_list(monkeypatch):
    monkeypatch.setattr(api.requests, "get", lambda *args, **kwargs: FakeResponse(200, {"items": []}))

    assert search_videos("asdfghjkl") == []


def test_missing_key_raises_error(monkeypatch):
    monkeypatch.setattr(api, "API_KEY", None)       # імітуємо порожній .env

    with pytest.raises(YouTubeAPIError, match="YOUTUBE_API_KEY"):
        search_videos("docker")
    # match перевіряє, що в тексті помилки є ці слова


def test_no_internet_raises_error(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError()  # «вимикаємо Wi-Fi» без вимикання Wi-Fi

    monkeypatch.setattr(api.requests, "get", fake_get)

    with pytest.raises(YouTubeAPIError, match="з'єднання"):
        search_videos("docker")


def test_timeout_raises_error(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(api.requests, "get", fake_get)

    with pytest.raises(YouTubeAPIError, match="не відповідає"):
        search_videos("docker")


def test_invalid_key_400_raises_error_with_details(monkeypatch):
    error_body = {"error": {"message": "API key not valid."}}
    monkeypatch.setattr(api.requests, "get", lambda *args, **kwargs: FakeResponse(400, error_body))

    with pytest.raises(YouTubeAPIError) as error_info:   # as дає доступ до самої помилки
        search_videos("docker")

    assert "400" in str(error_info.value)
    assert "API key not valid" in str(error_info.value)  # деталі від YouTube дійшли до користувача