"""RRG 引擎 — RS-Ratio / RS-Momentum / 象限归类。"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_rrg(
    sector_kline: pd.DataFrame,
    benchmark_kline: pd.DataFrame,
    window: int = 10,
    tail: int = 5,
) -> dict:
    """计算板块的 RS-Ratio 和 RS-Momentum。

    Args:
        sector_kline: 板块日线 DataFrame(date, close)，按日期升序
        benchmark_kline: 基准日线 DataFrame(date, close)，按日期升序
        window: 滚动窗口 (日)
        tail: 尾巴点数（暂时用于调用方过滤，引擎返回全量）

    Returns:
        {
            "dates": list[datetime],
            "rs_ratio": list[float],     # 横轴
            "rs_momentum": list[float],  # 纵轴
            "quadrant": list[str],       # "leading"|"improving"|"lagging"|"weakening"
        }

    Raises:
        ValueError: 有效数据点 < window * 2
    """
    # 对齐日期，取 inner join
    merged = sector_kline[["date", "close"]].merge(
        benchmark_kline[["date", "close"]],
        on="date",
        suffixes=("_s", "_b"),
    ).sort_values("date").reset_index(drop=True)

    n = len(merged)
    if n < window * 2:
        raise ValueError(
            f"数据不足: 仅 {n} 个有效日期, 需要 >= {window * 2}"
        )

    close_s = merged["close_s"].values
    close_b = merged["close_b"].values
    dates = merged["date"].tolist()

    # Step 1: RS = 100 * (P_s / P_b)
    rs = 100.0 * close_s / close_b

    # Step 2: RS-Ratio = 100 + (RS - MA(RS)) / Std(RS, ddof=1)
    rs_series = pd.Series(rs)
    rs_ma = rs_series.rolling(window=window, min_periods=window).mean()
    rs_std = rs_series.rolling(window=window, min_periods=window).std(ddof=1)
    rs_ratio = 100.0 + (rs_series - rs_ma) / rs_std.replace(0, np.nan)

    # Step 3: ROC = 100 * (RS-Ratio / RS-Ratio_lag1 - 1)
    roc = 100.0 * (rs_ratio / rs_ratio.shift(1) - 1.0)

    # Step 4: RS-Momentum = 101 + (ROC - MA(ROC)) / Std(ROC, ddof=1)
    roc_ma = roc.rolling(window=window, min_periods=window).mean()
    roc_std = roc.rolling(window=window, min_periods=window).std(ddof=1)
    rs_momentum = 101.0 + (roc - roc_ma) / roc_std.replace(0, np.nan)

    # Step 5: 四象限
    quadrant = []
    for rr, rm in zip(rs_ratio, rs_momentum):
        if pd.isna(rr) or pd.isna(rm):
            quadrant.append("unknown")
        elif rr < 100 and rm < 101:
            quadrant.append("lagging")
        elif rr >= 100 and rm >= 101:
            quadrant.append("leading")
        elif rr < 100 and rm >= 101:
            quadrant.append("improving")
        else:
            quadrant.append("weakening")

    # 只返回有效区间
    valid_mask = rs_ratio.notna() & rs_momentum.notna()
    return {
        "dates": [dates[i] for i in range(len(dates)) if valid_mask.iloc[i]],
        "rs_ratio": rs_ratio[valid_mask].tolist(),
        "rs_momentum": rs_momentum[valid_mask].tolist(),
        "quadrant": [quadrant[i] for i in range(len(quadrant)) if valid_mask.iloc[i]],
    }
