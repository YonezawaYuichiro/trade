"""J-Quants（Free）から日足を全営業日分取り、末尾6か月をホールドアウトとしてロックする。

使い方: uv run python tools/fetch_daily.py
APIキーは .env の JQUANTS_API_KEY=...（または環境変数）。収益率は計算しない。
途中で止まったら、同じコマンドで続きから取る。営業日の一覧とホールドアウト開始日は、最初の実行で
data/fetch_plan.json に固定する（cleanroom/fetch.py の run_fetch）。
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cleanroom.fetch import run_fetch  # noqa: E402
from cleanroom.jquants import JQuantsClient, load_api_key  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    parser.add_argument("--calendar-code", default="86970", help="営業日の一覧を取るための銘柄（公式サンプルの銘柄）")
    parser.add_argument("--holdout-months", type=int, default=6)
    args = parser.parse_args()

    client = JQuantsClient(load_api_key(ROOT / ".env"))
    summary = run_fetch(
        client,
        args.data,
        args.calendar_code,
        args.holdout_months,
        progress=lambda day, n: print(f"{day}: {n} 行", flush=True),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
