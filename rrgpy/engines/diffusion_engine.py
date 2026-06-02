"""扩散度引擎 — 市值加权上涨占比 + MA 平滑 + 趋势灯。"""
from __future__ import annotations

import numpy as np
import pandas as pd
from rrgpy.config import EXPANSION_THRESHOLD, CONTRACTION_THRESHOLD


def compute_diffusion(
    constituents_data: dict,
    ma_period: int = 20,
) -> dict:
    """计算板块的市值加权扩散度。

    Args:
        constituents_data: fetch_constituents_data() 的返回值
            {"stocks": [{code, float_shares}, ...],
             "klines": {code: DataFrame(date, close)}}
        ma_period: MA 平滑周期

    Returns:
        {
            "dates": list[datetime],
            "raw_diffusion": list[float | None],      # 原始扩散度
            "smoothed_diffusion": list[float | None], # MA 平滑后
            "trend_light": list[str],  # "expansion"|"contraction"|"neutral"|"unknown"
        }
    """
    stocks = constituents_data.get("stocks", [])
    klines = constituents_data.get("klines", {})

    if not stocks or not klines:
        return {
            "dates": [], "raw_diffusion": [],
            "smoothed_diffusion": [], "trend_light": [],
        }

    # 构建统一日期索引
    all_dates = set()
    for code in klines:
        all_dates.update(klines[code]["date"].tolist())
    all_dates = sorted(all_dates)

    if not all_dates:
        return {
            "dates": [], "raw_diffusion": [],
            "smoothed_diffusion": [], "trend_light": [],
        }

    # 流通市值加权扩散度计算
    raw_diffusion = []
    for date in all_dates:
        total_float_mcap = 0.0
        up_float_mcap = 0.0

        for stock in stocks:
            code = stock["code"]
            float_shares = stock.get("float_shares", 0) or 0
            if float_shares <= 0:
                continue
            if code not in klines:
                continue

            df = klines[code]
            # 找当天和前一天的收盘价
            day_data = df[df["date"] == date]
            if day_data.empty:
                continue
            close_today = float(day_data["close"].iloc[0])

            # 找前一个交易日
            prev_data = df[df["date"] < date]
            if prev_data.empty:
                continue
            close_prev = float(prev_data["close"].iloc[-1])

            if close_prev <= 0:
                continue

            float_mcap = float_shares * close_today
            total_float_mcap += float_mcap

            if close_today > close_prev:
                up_float_mcap += float_mcap

        if total_float_mcap > 0:
            raw_diff = (up_float_mcap / total_float_mcap) * 100.0
        else:
            raw_diff = None

        raw_diffusion.append(raw_diff)

    # MA 平滑
    raw_series = pd.Series(raw_diffusion, index=all_dates)
    smoothed = raw_series.rolling(window=ma_period, min_periods=1).mean()

    # 趋势灯
    trend_lights = []
    for i, date in enumerate(all_dates):
        val = smoothed.iloc[i]
        if pd.isna(val):
            trend_lights.append("unknown")
            continue

        # 5 日前值
        idx_5d = i - 5
        if idx_5d < 0:
            val_5d = val
        else:
            val_5d = smoothed.iloc[idx_5d]
            if pd.isna(val_5d):
                val_5d = val

        if val > val_5d and val > EXPANSION_THRESHOLD:
            trend_lights.append("expansion")
        elif val < val_5d and val < CONTRACTION_THRESHOLD:
            trend_lights.append("contraction")
        else:
            trend_lights.append("neutral")

    return {
        "dates": all_dates,
        "raw_diffusion": [None if pd.isna(v) else float(v) for v in raw_diffusion],
        "smoothed_diffusion": [None if pd.isna(v) else float(v) for v in smoothed],
        "trend_light": trend_lights,
    }
