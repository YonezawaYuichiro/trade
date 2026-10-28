"""J-Quants API V2 の取得コード（Free プラン向け）。

仕様: https://jpx-jquants.com/ja/spec/eq-bars-daily （本人が 2026-10-27 に写した文言、DATA.md）
- ヘッダ x-api-key に APIキー。続きがあるときは pagination_key。
- Free は 5件/分。数値は float を通さず Decimal で読む。
APIキーは表示、例外の文、URL に入れない。
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal
from pathlib import Path
from typing import Callable

import pandas as pd

from cleanroom.schema import TZ

BASE_URL = "https://api.jquants.com/v2"
FREE_MIN_INTERVAL = 13.0  # 5件/分に余裕を持たせた間隔（秒）
KEY_ENV = "JQUANTS_API_KEY"

Transport = Callable[[str, dict], tuple[int, bytes]]

_DECIMAL_FIELDS = {"O": "open", "H": "high", "L": "low", "C": "close", "AdjC": "adj_close", "AdjFactor": "adj_factor", "Vo": "volume"}
_FLAG_FIELDS = {"UL": "upper_limit", "LL": "lower_limit"}


class JQuantsError(RuntimeError):
    pass


def _urllib_transport(url: str, headers: dict) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return 0, b""


class JQuantsClient:
    def __init__(
        self,
        api_key: str,
        transport: Transport | None = None,
        sleep: Callable[[float], None] | None = None,
        clock: Callable[[], float] | None = None,
        min_interval: float = FREE_MIN_INTERVAL,
        max_retries: int = 5,
    ):
        import time

        self._key = api_key
        self._transport = transport or _urllib_transport
        self._sleep = sleep or time.sleep
        self._clock = clock or time.monotonic
        self._min_interval = min_interval
        self._max_retries = max_retries
        self._last_call: float | None = None

    def __repr__(self) -> str:
        return f"JQuantsClient(base={BASE_URL!r}, key=***)"

    def get(self, path: str, params: dict) -> list[dict]:
        """pagination_key が無くなるまで取り、data の配列をつなげて返す。"""
        params = dict(params)
        records: list[dict] = []
        seen: set[str] = set()
        while True:
            body = self._request(path, params)
            records.extend(body.get("data", []))
            next_key = body.get("pagination_key")
            if not next_key:
                return records
            if next_key in seen:
                raise JQuantsError(f"{path} が同じ pagination_key を繰り返し返した")
            seen.add(next_key)
            params["pagination_key"] = next_key

    def _wait_turn(self) -> None:
        if self._last_call is not None:
            wait = self._last_call + self._min_interval - self._clock()
            if wait > 0:
                self._sleep(wait)
        self._last_call = self._clock()

    def _request(self, path: str, params: dict) -> dict:
        url = f"{BASE_URL}{path}?{urllib.parse.urlencode(params)}"
        for attempt in range(self._max_retries + 1):
            self._wait_turn()
            status, raw = self._transport(url, {"x-api-key": self._key})
            if status == 200:
                return json.loads(raw, parse_float=Decimal, parse_int=Decimal)
            if status == 0 or status == 429 or status >= 500:
                self._sleep(min(60 * 2**attempt, 600))
                continue
            text = raw[:500].decode("utf-8", errors="replace")
            raise JQuantsError(f"{path} が HTTP {status} を返した: {text}")
        raise JQuantsError(f"{path} の再試行が上限（{self._max_retries} 回）に達した")


def load_api_key(dotenv: Path) -> str:
    """環境変数 JQUANTS_API_KEY、無ければ dotenv の JQUANTS_API_KEY=... の行から読む。"""
    value = os.environ.get(KEY_ENV, "").strip()
    if value:
        return value
    if Path(dotenv).exists():
        for line in Path(dotenv).read_text(encoding="utf-8").splitlines():
            name, sep, rest = line.strip().partition("=")
            if sep and name.strip() == KEY_ENV and rest.strip():
                return rest.strip().strip('"').strip("'")
    raise JQuantsError(f"{KEY_ENV} が見つからない。{dotenv} か環境変数に置く")


def _to_decimal(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, str):
        return Decimal(value)
    raise TypeError(f"Decimal にできない型: {type(value).__name__}（float は受け付けない）")


def to_bars(records: list[dict]) -> pd.DataFrame:
    """/equities/bars/daily の data を、validate_bars の形の表にする。

    ts は Date の 0:00 JST。終値が確定した時刻ではない（cleanroom/schema.py）。
    """
    rows = []
    for r in records:
        row = {"code": r["Code"], "ts": r["Date"]}
        row.update({col: _to_decimal(r[field]) for field, col in _DECIMAL_FIELDS.items()})
        row.update({col: r[field] for field, col in _FLAG_FIELDS.items()})
        rows.append(row)
    columns = ["code", "ts", *_DECIMAL_FIELDS.values(), *_FLAG_FIELDS.values()]
    df = pd.DataFrame(rows, columns=columns, dtype=object)
    df["ts"] = pd.to_datetime(df["ts"], format="%Y-%m-%d").dt.tz_localize(TZ)
    return df
