"""端到端集成测试（使用模拟数据，不需要网络）。"""
import pandas as pd
import numpy as np
from rrgpy.engines.rrg_engine import compute_rrg
from rrgpy.engines.diffusion_engine import compute_diffusion


def make_sector_kline(n_days: int = 60, trend: float = 0.02) -> pd.DataFrame:
    """生成模拟板块 K 线。"""
    dates = pd.date_range("2026-01-02", periods=n_days, freq="B")
    prices = [100.0]
    for _ in range(1, n_days):
        prices.append(prices[-1] * (1 + np.random.randn() * 0.02 + trend / 252))
    return pd.DataFrame({"date": dates, "close": prices})


def make_benchmark_kline(n_days: int = 60) -> pd.DataFrame:
    """生成模拟基准 K 线。"""
    dates = pd.date_range("2026-01-02", periods=n_days, freq="B")
    prices = [100.0]
    for _ in range(1, n_days):
        prices.append(prices[-1] * (1 + np.random.randn() * 0.015))
    return pd.DataFrame({"date": dates, "close": prices})


def make_constituents(n_stocks: int = 20, n_days: int = 60) -> dict:
    """生成模拟成分股数据。"""
    dates = pd.date_range("2026-01-02", periods=n_days, freq="B")
    np.random.seed(42)
    stocks = []
    klines = {}
    for i in range(n_stocks):
        code = f"00000{i}"
        stocks.append({
            "code": code, "name": f"股票{i}",
            "float_shares": float((i + 1) * 1000),
        })
        price = 10.0
        rows = []
        for d in dates:
            price *= (1 + np.random.randn() * 0.025)
            rows.append({"date": d, "close": round(max(price, 0.1), 2)})
        klines[code] = pd.DataFrame(rows)
    return {"stocks": stocks, "klines": klines}


def test_full_pipeline_rrg():
    """RRG 全流程: 数据 → 计算 → 结果可渲染。"""
    sector = make_sector_kline(60, trend=0.03)
    bench = make_benchmark_kline(60)
    result = compute_rrg(sector, bench, window=10, tail=5)

    assert len(result["dates"]) > 20  # ~30 valid after window
    assert len(result["rs_ratio"]) == len(result["dates"])
    assert len(result["rs_momentum"]) == len(result["dates"])
    assert len(result["quadrant"]) == len(result["dates"])
    # 最后一点不在 unknown
    assert result["quadrant"][-1] != "unknown"


def test_full_pipeline_diffusion():
    """扩散度全流程: 成分股 → 计算 → 结果合理。"""
    data = make_constituents(20, 60)
    result = compute_diffusion(data, ma_period=20)

    assert len(result["dates"]) == 60
    smoothed = [v for v in result["smoothed_diffusion"] if v is not None]
    assert len(smoothed) > 0
    assert all(0 <= v <= 100 for v in smoothed)
