"""扩散度引擎单元测试。"""
import pandas as pd
import numpy as np
import pytest
from rrgpy.engines.diffusion_engine import compute_diffusion


def make_test_constituents(
    n_stocks: int = 10,
    n_days: int = 40,
    up_ratio: float = 0.6,
) -> dict:
    """构造测试用成分股数据。"""
    dates = pd.date_range("2026-01-02", periods=n_days, freq="B")
    np.random.seed(42)
    stocks = []
    klines = {}
    for i in range(n_stocks):
        code = f"00000{i}"
        stocks.append({
            "code": code,
            "name": f"测试股{i}",
            "float_shares": float(1000 * (i + 1)),
        })
        # 价格走势: up_ratio 概率上涨
        price = 10.0
        rows = []
        for d in dates:
            if np.random.random() < up_ratio:
                price *= 1.02
            else:
                price *= 0.98
            rows.append({"date": d, "close": round(price, 2)})
        klines[code] = pd.DataFrame(rows)

    return {"stocks": stocks, "klines": klines}


def test_compute_diffusion_returns_correct_keys():
    """扩散度计算应返回所有必需 key。"""
    data = make_test_constituents(n_stocks=10, n_days=40)
    result = compute_diffusion(data, ma_period=20)

    assert "dates" in result
    assert "raw_diffusion" in result
    assert "smoothed_diffusion" in result
    assert "trend_light" in result
    assert len(result["dates"]) > 0


def test_compute_diffusion_value_range():
    """扩散度值应在 0-100 范围内。"""
    data = make_test_constituents(n_stocks=10, n_days=40)
    result = compute_diffusion(data, ma_period=20)

    smoothed = result["smoothed_diffusion"]
    valid = [v for v in smoothed if v is not None]
    assert all(0 <= v <= 100 for v in valid)


def test_compute_diffusion_trend_lights():
    """趋势灯应包含三种状态。"""
    data = make_test_constituents(n_stocks=10, n_days=40, up_ratio=0.8)
    result = compute_diffusion(data, ma_period=20)

    lights = [l for l in result["trend_light"] if l != "unknown"]
    assert set(lights).issubset({"expansion", "contraction", "neutral"})


def test_compute_diffusion_empty_constituents():
    """空成分股应返回空结果。"""
    data = {"stocks": [], "klines": {}}
    result = compute_diffusion(data, ma_period=20)
    assert len(result["dates"]) == 0


def test_compute_diffusion_insufficient_days():
    """不足 MA 周期的数据应正常返回（但趋势灯多为 unknown）。"""
    data = make_test_constituents(n_stocks=5, n_days=10)
    result = compute_diffusion(data, ma_period=20)
    # 10 < 20, 但不抛异常
    assert len(result["dates"]) > 0
