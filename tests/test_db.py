import sqlite3
import pytest
from db import init_db, save_videos, get_saved_videos


@pytest.fixture
def conn():
    """Фікстура: чиста база в пам'яті для КОЖНОГО тесту."""
    connection = sqlite3.connect(":memory:")          # база в оперативній пам'яті, youtube.db не чіпаємо
    connection.execute("PRAGMA foreign_keys = ON")
    init_db(connection)                               # створюємо таблиці channels і videos
    yield connection                                  # віддаємо базу тесту...
    connection.close()                                # ...а після тесту закриваємо


def make_item(video_id, channel_id, title="Video", channel_title="Channel"):
    """Створює «підробне» відео в тому ж форматі, що повертає YouTube API."""
    return {
        "id": {"videoId": video_id},
        "snippet": {
            "title": title,
            "channelId": channel_id,
            "channelTitle": channel_title,
            "publishedAt": "2025-01-01T00:00:00Z",
        },
    }


def count(conn, table):
    """Допоміжна функція: скільки рядків у таблиці."""
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    # f-string тут безпечний: назва таблиці — наш власний текст, а не введення користувача


def test_save_creates_rows(conn):
    items = [make_item("v1", "c1"), make_item("v2", "c2")]

    new_count = save_videos(conn, items)

    assert new_count == 2
    assert count(conn, "videos") == 2
    assert count(conn, "channels") == 2


def test_repeat_save_creates_no_duplicates(conn):
    items = [make_item("v1", "c1"), make_item("v2", "c1")]
    save_videos(conn, items)

    new_count = save_videos(conn, items)       # той самий пошук удруге

    assert new_count == 0                      # нових відео немає
    assert count(conn, "videos") == 2          # і рядків не побільшало


def test_channel_with_two_videos_saved_once(conn):
    items = [make_item("v1", "mosh"), make_item("v2", "mosh")]

    save_videos(conn, items)

    assert count(conn, "channels") == 1        # як Programming with Mosh: один канал, два відео
    assert count(conn, "videos") == 2


def test_get_saved_videos_joins_channel_title(conn):
    save_videos(conn, [make_item("v1", "c1", title="Docker 101", channel_title="TechWorld")])

    rows = get_saved_videos(conn)

    assert rows == [("TechWorld", "Docker 101", "2025-01-01T00:00:00Z", "v1")]
    # перше поле — назва каналу з таблиці channels, тобто JOIN спрацював


def test_foreign_key_blocks_video_without_channel(conn):
    with pytest.raises(sqlite3.IntegrityError):       # очікуємо, що база ВІДМОВИТЬ
        conn.execute(
            "INSERT INTO videos (id, title, channel_id) VALUES (?, ?, ?)",
            ("v1", "Orphan video", "no-such-channel"),
        )