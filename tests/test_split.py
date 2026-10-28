import hashlib
import json
from decimal import Decimal

import pandas as pd
import pytest

from cleanroom.schema import SchemaError, validate_bars
from cleanroom.split import (
    OPEN_CONFIRM,
    HoldoutLockedError,
    SplitPlan,
    assign_segments,
    load_bars,
    lock_holdout,
    lock_holdout_frames,
    open_holdout,
)
from conftest import make_bars, make_sessions

H = 5


@pytest.fixture
def plan() -> SplitPlan:
    s = make_sessions(300)
    return SplitPlan(valid_start=s[150], holdout_start=s[250], label_horizon=H)


def test_segments_keep_label_windows_apart(plan):
    sessions = make_sessions(300)
    seg = assign_segments(sessions, plan).to_numpy()
    idx = {name: [i for i, v in enumerate(seg) if v == name] for name in ("train", "valid", "holdout")}
    first_valid, first_holdout = idx["valid"][0], idx["holdout"][0]
    assert first_valid == 150 and first_holdout == 250
    # 学習のラベル期間 t+1..t+H は検証に入らず、その後ろに H 以上の余白がある
    last_train = idx["train"][-1]
    assert first_valid - (last_train + H) - 1 >= H
    last_valid = idx["valid"][-1]
    assert first_holdout - (last_valid + H) - 1 >= H
    assert idx["holdout"] == list(range(250, 300))
    assert set(seg) == {"train", "purge", "valid", "holdout"}


def test_segments_are_in_time_order(plan):
    seg = list(assign_segments(make_sessions(300), plan))
    order = {"train": 0, "valid": 1, "holdout": 2}
    ranks = [order[v] for v in seg if v != "purge"]
    assert ranks == sorted(ranks)


def test_normal_loader_does_not_return_holdout(plan, tmp_path):
    bars = make_bars(300)
    lock_holdout(bars, plan.holdout_start, tmp_path)
    loaded = load_bars(tmp_path)
    assert len(loaded) == 250
    assert loaded["ts"].max() < plan.holdout_start
    validate_bars(loaded)
    assert loaded["close"].tolist() == bars["close"].iloc[:250].tolist()


def test_holdout_rows_are_not_in_main_file(plan, tmp_path):
    lock_holdout(make_bars(300), plan.holdout_start, tmp_path)
    sessions = make_sessions(300)
    main_files = [p for p in tmp_path.rglob("*.csv") if "holdout" not in p.parts]
    assert main_files
    for p in main_files:
        text = p.read_text(encoding="utf-8")
        assert sessions[249].isoformat() in text  # 書式が合っていることの確認
        assert not any(ts.isoformat() in text for ts in sessions[250:])


def test_holdout_opens_once_with_confirmation(plan, tmp_path):
    lock_holdout(make_bars(300), plan.holdout_start, tmp_path)
    with pytest.raises(HoldoutLockedError):
        open_holdout(tmp_path, confirm="yes")
    opened = open_holdout(tmp_path, confirm=OPEN_CONFIRM)
    assert len(opened) == 50
    assert opened["ts"].min() >= plan.holdout_start
    assert isinstance(opened.at[opened.index[0], "close"], Decimal)
    with pytest.raises(HoldoutLockedError):
        open_holdout(tmp_path, confirm=OPEN_CONFIRM)


def test_holdout_changed_after_lock_is_refused(plan, tmp_path):
    lock_holdout(make_bars(300), plan.holdout_start, tmp_path)
    hold = tmp_path / "holdout" / "bars.csv"
    df = pd.read_csv(hold, dtype=str, keep_default_na=False)
    df.loc[0, "close"] = "1.0"
    df.to_csv(hold, index=False)
    with pytest.raises(HoldoutLockedError):
        open_holdout(tmp_path, confirm=OPEN_CONFIRM)
    assert not (tmp_path / "holdout" / "OPENED").exists()


def test_lock_refuses_to_overwrite(plan, tmp_path):
    lock_holdout(make_bars(300), plan.holdout_start, tmp_path)
    with pytest.raises(FileExistsError):
        lock_holdout(make_bars(300), plan.holdout_start, tmp_path)


def test_loader_rejects_holdout_rows_placed_in_main(plan, tmp_path):
    lock_holdout(make_bars(300), plan.holdout_start, tmp_path)
    main = next(p for p in tmp_path.rglob("*.csv") if "holdout" not in p.parts)
    leaked = pd.concat([pd.read_csv(main, dtype=str), pd.read_csv(tmp_path / "holdout" / "bars.csv", dtype=str)])
    leaked.to_csv(main, index=False)
    with pytest.raises(HoldoutLockedError):
        load_bars(tmp_path)


def test_loader_rejects_holdout_start_day_alone(plan, tmp_path):
    lock_holdout(make_bars(300), plan.holdout_start, tmp_path)
    main = tmp_path / "main" / "bars.csv"
    first = pd.read_csv(tmp_path / "holdout" / "bars.csv", dtype=str, keep_default_na=False).iloc[[0]]
    assert first["ts"].iloc[0] == plan.holdout_start.isoformat()
    pd.concat([pd.read_csv(main, dtype=str, keep_default_na=False), first]).to_csv(main, index=False)
    with pytest.raises(HoldoutLockedError):
        load_bars(tmp_path)


def test_loader_rejects_nan_written_in_file(plan, tmp_path):
    lock_holdout(make_bars(300), plan.holdout_start, tmp_path)
    main = tmp_path / "main" / "bars.csv"
    df = pd.read_csv(main, dtype=str, keep_default_na=False)
    df.loc[3, "close"] = "NaN"
    df.to_csv(main, index=False)
    with pytest.raises(SchemaError):
        load_bars(tmp_path)


def test_flag_column_null_survives_round_trip(plan, tmp_path):
    bars = make_bars(300)
    bars["upper_limit"] = ["0"] * 300
    bars.at[10, "upper_limit"] = None
    lock_holdout(bars, plan.holdout_start, tmp_path)
    loaded = load_bars(tmp_path)
    assert loaded.at[10, "upper_limit"] is None
    assert loaded.at[11, "upper_limit"] == "0"


def test_lock_from_daily_frames_matches_single_frame(plan, tmp_path):
    bars = make_bars(300)
    frames = [bars.iloc[i : i + 1] for i in range(len(bars))]
    lock_holdout_frames(frames, plan.holdout_start, tmp_path / "a")
    lock_holdout(bars, plan.holdout_start, tmp_path / "b")
    assert load_bars(tmp_path / "a").equals(load_bars(tmp_path / "b"))
    assert len(open_holdout(tmp_path / "a", confirm=OPEN_CONFIRM)) == 50


def test_lock_refuses_invalid_frame(plan, tmp_path):
    bad = make_bars(300)
    bad.at[260, "close"] = Decimal("NaN")
    with pytest.raises(SchemaError):
        lock_holdout_frames([bad.iloc[:250], bad.iloc[250:]], plan.holdout_start, tmp_path)
    assert not (tmp_path / "plan.json").exists()


def test_invalid_holdout_is_refused_before_opening_is_used_up(plan, tmp_path):
    # ロックの検査をすり抜けた不正な行があっても、1回きりの開封を消費しない
    lock_holdout(make_bars(300), plan.holdout_start, tmp_path)
    hold = tmp_path / "holdout" / "bars.csv"
    df = pd.read_csv(hold, dtype=str, keep_default_na=False)
    df.loc[0, "close"] = "NaN"
    df.to_csv(hold, index=False)
    plan_path = tmp_path / "plan.json"
    saved = json.loads(plan_path.read_text(encoding="utf-8"))
    saved["holdout_sha256"] = hashlib.sha256(hold.read_bytes()).hexdigest()
    plan_path.write_text(json.dumps(saved), encoding="utf-8")
    with pytest.raises(SchemaError):
        open_holdout(tmp_path, confirm=OPEN_CONFIRM)
    assert not (tmp_path / "holdout" / "OPENED").exists()
