"""取得の手順。偽物のクライアントで、実際のAPIには送らない。"""
import hashlib
import json

import pandas as pd
import pytest

from cleanroom.fetch import (
    FetchError,
    build_store,
    fetch_days,
    holdout_start_for,
    load_or_fix_plan,
    run_fetch,
    session_dates,
)
from cleanroom.split import OPEN_CONFIRM, load_bars, open_holdout
from conftest import make_sessions
from test_jquants import sample


class FakeClient:
    def __init__(self, sessions, empty_dates=()):
        self.sessions = sessions
        self.empty_dates = set(empty_dates)
        self.calls = []

    def get(self, path, params):
        self.calls.append((path, dict(params)))
        if "code" in params:
            return [sample(Date=s.date().isoformat(), Code=params["code"]) for s in self.sessions]
        if params["date"] in self.empty_dates:
            return []
        return [sample(Date=params["date"], Code=code) for code in ("13010", "86970")]


def test_session_dates_come_from_one_code_and_keep_only_dates():
    sessions = make_sessions(20)
    fake = FakeClient(sessions)
    assert session_dates(fake, "86970") == list(sessions)
    assert fake.calls == [("/equities/bars/daily", {"code": "86970"})]


def test_holdout_is_the_last_six_months():
    sessions = list(make_sessions(500))
    start = holdout_start_for(sessions, months=6)
    cutoff = sessions[-1] - pd.DateOffset(months=6)
    inside = [s for s in sessions if s >= start]
    before = [s for s in sessions if s < start]
    assert all(s > cutoff for s in inside)
    assert before[-1] <= cutoff


def test_plan_is_fixed_once_and_reused(tmp_path):
    first = list(make_sessions(300))
    sessions, start = load_or_fix_plan(FakeClient(first), tmp_path / "plan.json", "86970", months=6)
    assert sessions == first and start == holdout_start_for(first, months=6)
    later = FakeClient(list(make_sessions(320)))  # 中断の後、APIの範囲が進んだ
    again_sessions, again_start = load_or_fix_plan(later, tmp_path / "plan.json", "86970", months=6)
    assert again_sessions == first and again_start == start
    assert later.calls == []


def test_fetch_days_separates_holdout_files_and_resumes(tmp_path):
    sessions = list(make_sessions(10))
    fake = FakeClient(sessions)
    fetch_days(fake, sessions, holdout_start=sessions[7], raw_dir=tmp_path)
    assert len(list((tmp_path / "main").glob("*.json"))) == 7
    assert len(list((tmp_path / "holdout").glob("*.json"))) == 3
    assert len(fake.calls) == 10
    fetch_days(fake, sessions, holdout_start=sessions[7], raw_dir=tmp_path)
    assert len(fake.calls) == 10
    saved = json.loads((tmp_path / "main" / f"{sessions[0].date().isoformat()}.json").read_text(encoding="utf-8"))
    assert saved[0]["C"] == "2045.0"  # Decimal は文字列で保存し、float にしない


def test_empty_day_is_an_error_and_is_not_saved(tmp_path):
    sessions = list(make_sessions(5))
    day = sessions[2].date().isoformat()
    with pytest.raises(FetchError):
        fetch_days(FakeClient(sessions, empty_dates=[day]), sessions, sessions[4], tmp_path)
    assert not (tmp_path / "main" / f"{day}.json").exists()
    fake = FakeClient(sessions)
    fetch_days(fake, sessions, sessions[4], tmp_path)
    assert [c[1]["date"] for c in fake.calls] == [day, sessions[3].date().isoformat(), sessions[4].date().isoformat()]


def test_saved_files_on_wrong_side_of_holdout_are_an_error(tmp_path):
    sessions = list(make_sessions(10))
    fetch_days(FakeClient(sessions), sessions, sessions[7], tmp_path)
    with pytest.raises(FetchError):
        fetch_days(FakeClient(sessions), sessions, sessions[8], tmp_path)  # 開始日がずれた
    with pytest.raises(FetchError):
        fetch_days(FakeClient(sessions), sessions, sessions[6], tmp_path)


def test_build_store_locks_holdout_and_hashes_files(tmp_path):
    sessions = list(make_sessions(10))
    fetch_days(FakeClient(sessions), sessions, holdout_start=sessions[7], raw_dir=tmp_path / "raw")
    summary = build_store(tmp_path / "raw", sessions[7], tmp_path / "store", sessions)
    loaded = load_bars(tmp_path / "store")
    assert loaded["ts"].max() < sessions[7]
    assert len(loaded) == 14
    assert summary["rows_main"] == 14 and summary["rows_holdout"] == 6
    assert summary["first"] == sessions[0].date().isoformat() and summary["last"] == sessions[-1].date().isoformat()
    manifest = pd.read_csv(tmp_path / "store" / "manifest.csv", dtype=str)
    assert len(manifest) == 10
    for row in manifest.itertuples():
        assert row.sha256 == hashlib.sha256((tmp_path / "raw" / row.file).read_bytes()).hexdigest()
    assert len(open_holdout(tmp_path / "store", confirm=OPEN_CONFIRM)) == 6


def test_build_store_refuses_missing_or_empty_day(tmp_path):
    sessions = list(make_sessions(6))
    fetch_days(FakeClient(sessions), sessions, sessions[4], tmp_path / "raw")
    (tmp_path / "raw" / "main" / f"{sessions[1].date().isoformat()}.json").unlink()
    with pytest.raises(FetchError):
        build_store(tmp_path / "raw", sessions[4], tmp_path / "store", sessions)
    (tmp_path / "raw" / "main" / f"{sessions[1].date().isoformat()}.json").write_text("[]", encoding="utf-8")
    with pytest.raises(FetchError):
        build_store(tmp_path / "raw", sessions[4], tmp_path / "store2", sessions)


def test_run_fetch_leaves_no_raw_holdout_outside_lock(tmp_path):
    sessions = list(make_sessions(300))
    fake = FakeClient(sessions)
    summary = run_fetch(fake, tmp_path, "86970", months=6)
    assert summary["rows_holdout"] > 0
    assert list((tmp_path / "raw").rglob("holdout/*.json")) == []
    manifest = pd.read_csv(tmp_path / "store" / "manifest.csv", dtype=str)
    assert manifest["file"].str.startswith("holdout/").sum() == summary["n_sessions"] - len(list((tmp_path / "raw" / "main").glob("*.json")))
    assert json.loads((tmp_path / "store" / "fetch_summary.json").read_text(encoding="utf-8"))["rows_main"] == summary["rows_main"]


def test_run_fetch_does_not_refetch_after_lock(tmp_path):
    sessions = list(make_sessions(300))
    run_fetch(FakeClient(sessions), tmp_path, "86970", months=6)
    again = FakeClient(sessions)
    with pytest.raises(FileExistsError):
        run_fetch(again, tmp_path, "86970", months=6)
    assert again.calls == []


def test_run_fetch_after_lock_removes_leftover_raw_holdout(tmp_path):
    # ロックの後、raw/holdout を消す前に止まった場合。次の実行は取得せずに止まり、残りを消す
    sessions = list(make_sessions(300))
    run_fetch(FakeClient(sessions), tmp_path, "86970", months=6)
    leftover = tmp_path / "raw" / "holdout" / f"{sessions[-1].date().isoformat()}.json"
    leftover.write_text("[]", encoding="utf-8")
    again = FakeClient(sessions)
    with pytest.raises(FileExistsError):
        run_fetch(again, tmp_path, "86970", months=6)
    assert not leftover.exists()
    assert again.calls == []
