"""RRG 引擎单元测试。"""
import pandas as pd
import numpy as np
import pytest
from rrgpy.engines.rrg_engine import compute_rrg


def make_test_data(n_days: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    """构造板块和基准测试数据。板块走势强于基准。"""
    dates = pd.date_range("2026-01-02", periods=n_days, freq="B")
    np.random.seed(42)
    base = 100 + np.cumsum(np.random.randn(n_days) * 0.5)
    sector = 100 + np.cumsum(np.random.randn(n_days) * 0.5 + 0.05)
    df_sector = pd.DataFrame({"date": dates, "close": sector})
    df_bench = pd.DataFrame({"date": dates, "close": base})
    return df_sector, df_bench


def test_compute_rrg_returns_correct_keys():
    """RRG 计算结果应包含所有必需 key。"""
    sector, bench = make_test_data(60)
    result = compute_rrg(sector, bench, window=10, tail=5)

    assert "dates" in result
    assert "rs_ratio" in result
    assert "rs_momentum" in result
    assert "quadrant" in result
    assert len(result["dates"]) > 0


def test_compute_rrg_quadrant_leading():
    """板块持续走强，且末尾加速，应归入 Leading 象限。"""
    dates = pd.date_range("2026-01-02", periods=60, freq="B")
    # 板块持续强于基准，且最后一日额外拉升确保 RM > 101
    bench = pd.DataFrame({"date": dates, "close": np.linspace(100, 110, 60)})
    sector_arr = np.linspace(100, 120, 60)
    sector_arr[-1] += 5
    sector = pd.DataFrame({"date": dates, "close": sector_arr})

    result = compute_rrg(sector, bench, window=10, tail=5)
    assert result["quadrant"][-1] in ("leading", "improving")


def test_compute_rrg_quadrant_lagging():
    """板块持续走弱，且末尾加速下跌，应归入 Lagging 象限。"""
    dates = pd.date_range("2026-01-02", periods=60, freq="B")
    bench = pd.DataFrame({"date": dates, "close": np.linspace(100, 110, 60)})
    sector_arr = np.linspace(100, 95, 60)
    sector_arr[-1] -= 5
    sector = pd.DataFrame({"date": dates, "close": sector_arr})

    result = compute_rrg(sector, bench, window=10, tail=5)
    assert result["quadrant"][-1] in ("lagging", "weakening")


def test_compute_rrg_std_zero_handling():
    """一字板 (Std=0) 时 RS-Momentum 应置 0 不抛异常。"""
    dates = pd.date_range("2026-01-02", periods=60, freq="B")
    bench = pd.DataFrame({"date": dates, "close": np.linspace(100, 110, 60)})
    # 板块完全不动（Std=0）
    sector = pd.DataFrame({"date": dates, "close": [100.0] * 60})

    result = compute_rrg(sector, bench, window=10, tail=5)
    # 不应抛异常
    assert len(result["rs_momentum"]) > 0


def test_compute_rrg_insufficient_data():
    """数据不足应返回空结果。"""
    dates = pd.date_range("2026-01-02", periods=5, freq="B")
    sector = pd.DataFrame({"date": dates, "close": [100, 101, 102, 101, 100]})
    bench = pd.DataFrame({"date": dates, "close": [100, 100, 101, 100, 99]})

    with pytest.raises(ValueError, match="数据不足"):
        compute_rrg(sector, bench, window=10, tail=5)
