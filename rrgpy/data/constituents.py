"""板块成分股数据获取。"""
from __future__ import annotations

import time
import pandas as pd
from rrgpy.config import (
    CLIST_URL, KLIN_URL, REQUEST_TIMEOUT,
    RETRY_COUNT, RETRY_DELAY, BATCH_SIZE, LOOKBACK, get_session,
)


def fetch_constituent_list(sector_code: str) -> list[dict]:
    """拉取板块成分股列表（含流通股数）。

    Returns:
        [{code: "688017", name: "绿的谐波", float_shares: 1234567}, ...]
    """
    params = {
        "pn": "1",
        "pz": "500",
        "po": "1",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fs": f"b:{sector_code}+t:2",
        "fields": "f2,f3,f12,f14,f85",
    }
    r = get_session().get(CLIST_URL, params=params, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    data = r.json()

    items = data.get("data", {}).get("diff", [])
    stocks = []
    for item in items:
        code = item.get("f12", "")
        if not code:
            continue
        stocks.append({
            "code": code,
            "name": item.get("f14", ""),
            "float_shares": item.get("f85", 0) or 0,
        })
    return stocks


def _fetch_stock_kline(stock_code: str,
                       lookback: int = LOOKBACK) -> pd.DataFrame | None:
    """拉取单只个股日线 K 线。

    Returns:
        DataFrame(date, close) 或 None（失败时）
    """
    # 判断市场
    if stock_code.startswith("6"):
        secid = f"1.{stock_code}"
    else:
        secid = f"0.{stock_code}"

    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "1",
        "end": "20500101",
        "lmt": str(lookback),
    }

    for attempt in range(RETRY_COUNT + 1):
        try:
            r = get_session().get(KLIN_URL, params=params,
                                  timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            d = r.json()
            break
        except Exception:
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
            else:
                return None

    klines = d.get("data", {}).get("klines", [])
    if not klines:
        return None

    rows = []
    for line in klines:
        parts = line.split(",")
        if len(parts) < 3:
            continue
        rows.append({
            "date": parts[0],
            "close": float(parts[2]),
        })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def fetch_constituents_data(
    sector_code: str,
    lookback: int = LOOKBACK,
) -> dict:
    """拉取板块成分股完整数据。

    Returns:
        {
            "stocks": [{code, name, float_shares}, ...],
            "klines": {code: DataFrame(date, close)},
        }
    """
    stocks = fetch_constituent_list(sector_code)
    if not stocks:
        return {"stocks": [], "klines": {}}

    klines = {}
    # 串行拉取，非交易时段可承受；如需加速可改 ThreadPoolExecutor
    for stock in stocks:
        df = _fetch_stock_kline(stock["code"], lookback)
        if df is not None:
            klines[stock["code"]] = df

    return {"stocks": stocks, "klines": klines}
