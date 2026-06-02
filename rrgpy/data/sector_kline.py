"""板块 + 基准 K 线获取。"""
from __future__ import annotations

import time
import pandas as pd
import requests
from rrgpy.config import (
    KLIN_URL, BENCHMARK_SECID, UA, REQUEST_TIMEOUT,
    RETRY_COUNT, RETRY_DELAY, LOOKBACK,
)


def _fetch_kline(secid: str, lookback: int = LOOKBACK) -> pd.DataFrame:
    """拉取单只标的日线 K 线。

    Args:
        secid: 东财格式 "90.BK0425" (板块) 或 "1.830000" (指数)
        lookback: 回看天数

    Returns:
        DataFrame with columns: date, open, close, high, low, volume
        按日期升序排列
    """
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",    # 日线
        "fqt": "1",      # 前复权
        "end": "20500101",
        "lmt": str(lookback),
    }
    headers = {"User-Agent": UA}

    for attempt in range(RETRY_COUNT + 1):
        try:
            r = requests.get(KLIN_URL, params=params, headers=headers,
                             timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            d = r.json()
            break
        except Exception:
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
            else:
                raise

    klines = d.get("data", {}).get("klines", [])
    if not klines:
        return pd.DataFrame()

    rows = []
    for line in klines:
        parts = line.split(",")
        if len(parts) < 6:
            continue
        rows.append({
            "date": parts[0],
            "open": float(parts[1]),
            "close": float(parts[2]),
            "high": float(parts[3]),
            "low": float(parts[4]),
            "volume": float(parts[5]),
        })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def fetch_sector_klines(sector_codes: list[str],
                        lookback: int = LOOKBACK) -> dict[str, pd.DataFrame]:
    """批量拉取板块 K 线。

    Args:
        sector_codes: 板块代码列表 ["BK0425", "BK0429", ...]
        lookback: 回看天数

    Returns:
        {sector_code: DataFrame(date, open, close, high, low, volume)}
    """
    result = {}
    for code in sector_codes:
        secid = f"90.{code}"
        try:
            df = _fetch_kline(secid, lookback)
            if not df.empty:
                result[code] = df
        except Exception:
            continue
    return result


def fetch_benchmark_kline(lookback: int = LOOKBACK) -> pd.DataFrame:
    """拉取基准 830000 K 线。

    Returns:
        DataFrame with columns: date, close
    """
    df = _fetch_kline(BENCHMARK_SECID, lookback)
    if df.empty:
        raise RuntimeError(f"基准 {BENCHMARK_SECID} K 线获取失败")
    return df[["date", "close"]].copy()
