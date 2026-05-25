from datetime import date, datetime

from pomo.ratings import (
    Rating,
    load_ratings,
    rating_for_date,
    ratings_in_range,
    save_ratings,
    upsert_rating,
)


def _rating(day: str = "2026-05-25", score: int = 4, comment: str = "") -> Rating:
    return Rating(
        date=day,
        score=score,
        comment=comment,
        recorded_at=day + "T22:00:00",
    )


def test_load_missing_file_returns_empty(tmp_path):
    assert load_ratings(tmp_path / "ratings.json") == []


def test_save_then_load_roundtrip(tmp_path):
    path = tmp_path / "ratings.json"
    save_ratings(path, [_rating("2026-05-24", 3, "一般"), _rating("2026-05-25", 5)])
    loaded = load_ratings(path)
    assert [(r.date, r.score, r.comment) for r in loaded] == [
        ("2026-05-24", 3, "一般"),
        ("2026-05-25", 5, ""),
    ]


def test_save_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "dir" / "ratings.json"
    save_ratings(path, [_rating()])
    assert path.exists()


def test_upsert_appends_for_new_date(tmp_path):
    path = tmp_path / "ratings.json"
    upsert_rating(path, _rating("2026-05-24", 3))
    upsert_rating(path, _rating("2026-05-25", 5))
    loaded = load_ratings(path)
    assert sorted(r.date for r in loaded) == ["2026-05-24", "2026-05-25"]


def test_upsert_overwrites_same_date(tmp_path):
    path = tmp_path / "ratings.json"
    upsert_rating(path, _rating("2026-05-25", 2, "一开始觉得不太好"))
    upsert_rating(path, _rating("2026-05-25", 5, "其实做完看挺满意"))
    loaded = load_ratings(path)
    assert len(loaded) == 1
    assert loaded[0].score == 5
    assert loaded[0].comment == "其实做完看挺满意"


def test_load_corrupt_file_returns_empty(tmp_path):
    path = tmp_path / "ratings.json"
    path.write_text("{ this is not valid json", encoding="utf-8")
    assert load_ratings(path) == []


def test_save_backs_up_corrupt_file(tmp_path):
    path = tmp_path / "ratings.json"
    path.write_text("{ corrupt", encoding="utf-8")
    save_ratings(path, [_rating()])
    backup = tmp_path / "ratings.json.bak"
    assert backup.exists()


def test_load_non_object_json_returns_empty(tmp_path):
    path = tmp_path / "ratings.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    assert load_ratings(path) == []


def test_rating_for_date_finds_or_returns_none():
    ratings = [_rating("2026-05-24", 3), _rating("2026-05-25", 5)]
    found = rating_for_date(ratings, date(2026, 5, 25))
    assert found is not None and found.score == 5
    assert rating_for_date(ratings, date(2026, 5, 26)) is None


def test_ratings_in_range_filters_and_sorts():
    ratings = [
        _rating("2026-05-26", 5),
        _rating("2026-05-22", 2),
        _rating("2026-05-24", 4),
        _rating("2026-05-30", 1),  # 超出区间
    ]
    inside = ratings_in_range(ratings, date(2026, 5, 22), date(2026, 5, 28))
    assert [r.date for r in inside] == ["2026-05-22", "2026-05-24", "2026-05-26"]


def test_rating_create_uses_iso_date_and_recorded_at():
    now = datetime(2026, 5, 25, 21, 30, 12)
    r = Rating.create(day=now.date(), score=4, comment="还行", now=now)
    assert r.date == "2026-05-25"
    assert r.recorded_at.startswith("2026-05-25T21:30:12")
    assert r.score == 4
    assert r.comment == "还行"


def test_legacy_record_without_comment_field_loads(tmp_path):
    path = tmp_path / "ratings.json"
    path.write_text(
        '{"version": 1, "ratings": [{'
        '"date": "2026-05-22", "score": 3, '
        '"recorded_at": "2026-05-22T20:00:00"}]}',
        encoding="utf-8",
    )
    loaded = load_ratings(path)
    assert len(loaded) == 1
    assert loaded[0].comment == ""
