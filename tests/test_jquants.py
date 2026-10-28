"""J-Quants の取得コード。通信は偽物で置き換え、実際のAPIには送らない。"""
import json
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest

from cleanroom.jquants import FREE_MIN_INTERVAL, JQuantsClient, JQuantsError, load_api_key, to_bars
from cleanroom.schema import TZ, validate_bars

KEY = "secret-key-for-test"

# 公式の仕様ページのレスポンスサンプル（Free で返らない前場・後場の項目は除いた）
SAMPLE_JSON = """{
  "Date": "2023-03-24", "Code": "86970",
  "O": 2047.0, "H": 2069.0, "L": 2035.0, "C": 2045.0, "UL": "0", "LL": "0",
  "Vo": 2202500.0, "Va": 4507051850.0, "AdjFactor": 1.0,
  "AdjO": 2047.0, "AdjH": 2069.0, "AdjL": 2035.0, "AdjC": 2045.0, "AdjVo": 2202500.0,
  "MktCap": 1083850.0, "ExRT": null
}"""


def sample(**changes) -> dict:
    record = json.loads(SAMPLE_JSON, parse_float=Decimal)
    record.update(changes)
    return record


def page(records_json: list[str], key: str | None = None) -> bytes:
    tail = f', "pagination_key": "{key}"' if key else ""
    return ('{"data": [' + ", ".join(records_json) + "]" + tail + "}").encode()


class FakeTransport:
    def __init__(self, responses, clock):
        self.responses = list(responses)
        self.calls = []
        self.clock = clock

    def __call__(self, url, headers):
        self.calls.append((url, dict(headers), self.clock.now()))
        return self.responses.pop(0)


class FakeClock:
    def __init__(self):
        self.t = 1000.0
        self.slept = []

    def now(self):
        return self.t

    def sleep(self, dt):
        self.slept.append(dt)
        self.t += dt


def client(responses):
    clock = FakeClock()
    transport = FakeTransport(responses, clock)
    return JQuantsClient(KEY, transport=transport, sleep=clock.sleep, clock=clock.now), transport, clock


def test_numbers_are_parsed_as_decimal_not_float():
    c, _, _ = client([(200, page([SAMPLE_JSON]))])
    rec = c.get("/equities/bars/daily", {"code": "86970", "date": "2023-03-24"})[0]
    for key in ("O", "H", "L", "C", "Vo", "AdjFactor", "AdjC"):
        assert isinstance(rec[key], Decimal), key
    assert rec["C"] == Decimal("2045.0")
    assert rec["ExRT"] is None


def test_pagination_is_followed_until_key_disappears():
    c, t, _ = client([(200, page([SAMPLE_JSON], key="p2")), (200, page([SAMPLE_JSON], key="p3")), (200, page([]))])
    records = c.get("/equities/bars/daily", {"date": "2023-03-24"})
    assert len(records) == 2
    assert len(t.calls) == 3
    second = parse_qs(urlparse(t.calls[1][0]).query)
    assert second == {"date": ["2023-03-24"], "pagination_key": ["p2"]}
    assert parse_qs(urlparse(t.calls[2][0]).query)["pagination_key"] == ["p3"]


def test_request_goes_to_official_endpoint_with_key_in_header_only():
    c, t, _ = client([(200, page([]))])
    c.get("/equities/bars/daily", {"code": "86970"})
    url, headers, _ = t.calls[0]
    assert url.startswith("https://api.jquants.com/v2/equities/bars/daily?")
    assert headers == {"x-api-key": KEY}
    assert KEY not in url
    assert KEY not in repr(c)


def test_calls_are_spaced_for_free_plan_limit():
    assert FREE_MIN_INTERVAL >= 12  # 公式: Free は 5件/分
    c, t, _ = client([(200, page([], key=f"p{i}")) for i in range(3)] + [(200, page([]))])
    c.get("/equities/bars/daily", {"date": "2023-03-24"})
    times = [call[2] for call in t.calls]
    assert all(b - a >= FREE_MIN_INTERVAL for a, b in zip(times, times[1:]))


@pytest.mark.parametrize("status", [429, 500, 503, 0])
def test_retryable_errors_wait_then_succeed(status):
    c, t, clock = client([(status, b""), (200, page([SAMPLE_JSON]))])
    assert len(c.get("/equities/bars/daily", {"date": "2023-03-24"})) == 1
    assert len(t.calls) == 2
    assert t.calls[1][2] - t.calls[0][2] >= 60


def test_gives_up_after_retries():
    c, _, _ = client([(503, b"")] * 10)
    with pytest.raises(JQuantsError):
        c.get("/equities/bars/daily", {"date": "2023-03-24"})


def test_bad_request_raises_with_message_but_not_key():
    c, t, _ = client([(400, '{"message": "取得可能範囲外です"}'.encode())])
    with pytest.raises(JQuantsError) as err:
        c.get("/equities/bars/daily", {"date": "2000-01-04"})
    assert "取得可能範囲外" in str(err.value)
    assert KEY not in str(err.value)
    assert len(t.calls) == 1


def test_to_bars_maps_official_fields():
    bars = to_bars([sample()])
    validate_bars(bars)
    row = bars.iloc[0]
    assert row["code"] == "86970"
    assert row["ts"] == pd.Timestamp("2023-03-24", tz=TZ)
    assert row["open"] == Decimal("2047.0") and row["close"] == Decimal("2045.0")
    assert row["adj_close"] == Decimal("2045.0") and row["adj_factor"] == Decimal("1.0")
    assert row["volume"] == Decimal("2202500.0")
    assert row["upper_limit"] == "0" and row["lower_limit"] == "0"


def test_to_bars_accepts_decimal_strings_from_saved_files():
    rec = {k: (str(v) if isinstance(v, Decimal) else v) for k, v in sample().items()}
    assert to_bars([rec]).iloc[0]["close"] == Decimal("2045.0")


def test_to_bars_rejects_float():
    with pytest.raises(TypeError):
        to_bars([sample(C=2045.0)])


def test_to_bars_keeps_null_day_as_none():
    nulls = {k: None for k in ("O", "H", "L", "C", "Vo", "Va", "AdjO", "AdjH", "AdjL", "AdjC", "AdjVo", "UL", "LL")}
    bars = to_bars([sample(**nulls)])
    validate_bars(bars)
    assert all(bars.iloc[0][c] is None for c in ("open", "high", "low", "close", "adj_close", "volume"))


def test_api_key_from_env_then_dotenv(tmp_path, monkeypatch):
    monkeypatch.setenv("JQUANTS_API_KEY", "from-env")
    assert load_api_key(tmp_path / ".env") == "from-env"
    monkeypatch.delenv("JQUANTS_API_KEY")
    (tmp_path / ".env").write_text("# comment\nJQUANTS_API_KEY=from-file\n", encoding="utf-8")
    assert load_api_key(tmp_path / ".env") == "from-file"


def test_missing_api_key_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("JQUANTS_API_KEY", raising=False)
    with pytest.raises(JQuantsError):
        load_api_key(tmp_path / ".env")


def test_repeated_pagination_key_stops():
    c, t, _ = client([(200, page([SAMPLE_JSON], key="same"))] * 5)
    with pytest.raises(JQuantsError):
        c.get("/equities/bars/daily", {"date": "2023-03-24"})
    assert len(t.calls) == 2
