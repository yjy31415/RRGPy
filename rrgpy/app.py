"""A股板块 RRG + 扩散度分析 — Streamlit 主应用。"""
from __future__ import annotations

import streamlit as st

from rrgpy.config import (
    BENCHMARK_CODE, BENCHMARK_NAME,
    WINDOW, TAIL, LOOKBACK, DIFFUSION_MA,
)
from rrgpy.data.sector_list import fetch_sector_list
from rrgpy.data.sector_kline import fetch_sector_klines, fetch_benchmark_kline
from rrgpy.data.constituents import fetch_constituents_data
from rrgpy.engines.rrg_engine import compute_rrg
from rrgpy.engines.diffusion_engine import compute_diffusion
from rrgpy.ui.rrg_chart import build_rrg_chart
from rrgpy.ui.diffusion_chart import build_diffusion_chart
from rrgpy.ui.ranking_table import build_ranking_table, render_ranking_table


st.set_page_config(
    page_title="板块 RRG + 扩散度分析",
    page_icon="📊",
    layout="wide",
)


# ── Session State 初始化 ──────────────────────────────
if "sector_list" not in st.session_state:
    st.session_state.sector_list = None
if "benchmark_kline" not in st.session_state:
    st.session_state.benchmark_kline = None
if "sector_klines" not in st.session_state:
    st.session_state.sector_klines = {}
if "constituents_data" not in st.session_state:
    st.session_state.constituents_data = {}
if "rrg_results" not in st.session_state:
    st.session_state.rrg_results = {}
if "diffusion_results" not in st.session_state:
    st.session_state.diffusion_results = {}
if "selected_sectors" not in st.session_state:
    st.session_state.selected_sectors = []
if "last_params" not in st.session_state:
    st.session_state.last_params = {"window": 0, "tail": 0, "lookback": 0, "diffusion_ma": 0}


# ── 侧边栏 ─────────────────────────────────────────────
with st.sidebar:
    st.title("📊 板块 RRG + 扩散度")

    st.markdown(f"**基准:** {BENCHMARK_CODE} ({BENCHMARK_NAME})")

    col1, col2 = st.columns(2)
    with col1:
        window = st.number_input("窗口 (日)", min_value=3, max_value=30,
                                 value=WINDOW, step=1)
    with col2:
        tail = st.number_input("尾巴 (点)", min_value=1, max_value=15,
                               value=TAIL, step=1)

    lookback = st.number_input("回看期 (日)", min_value=20, max_value=250,
                               value=LOOKBACK, step=10)

    diffusion_ma = st.slider("扩散度 MA", min_value=5, max_value=60,
                             value=DIFFUSION_MA, step=1)

    st.divider()

    # 加载板块列表
    if st.session_state.sector_list is None:
        with st.spinner("加载板块列表..."):
            try:
                st.session_state.sector_list = fetch_sector_list()
            except Exception as e:
                st.error(f"板块列表加载失败: {e}")

    if st.session_state.sector_list:
        sectors = st.session_state.sector_list
        sector_names = [s["name"] for s in sectors]

        # 快捷筛选
        st.caption("快捷筛选")
        qcol1, qcol2 = st.columns(2)
        with qcol1:
            if st.button("📈 涨幅 TOP 20", use_container_width=True):
                top20 = sorted(sectors, key=lambda x: x.get("change_pct", 0),
                               reverse=True)[:20]
                st.session_state.selected_sectors = [s["name"] for s in top20]
        with qcol2:
            if st.button("📉 跌幅 TOP 10", use_container_width=True):
                bottom10 = sorted(sectors, key=lambda x: x.get("change_pct", 0))[:10]
                st.session_state.selected_sectors = [s["name"] for s in bottom10]

        if st.button("🔄 全选", use_container_width=True):
            st.session_state.selected_sectors = sector_names.copy()

        if st.button("🗑️ 清空", use_container_width=True):
            st.session_state.selected_sectors = []

        # 板块多选
        st.divider()
        st.caption(f"板块选择 ({len(st.session_state.selected_sectors)}/{len(sectors)} 已选)")

        selected = st.multiselect(
            "搜索/选择板块",
            options=sector_names,
            default=st.session_state.selected_sectors,
            label_visibility="collapsed",
            key="sector_multiselect",
        )
        st.session_state.selected_sectors = selected

    st.divider()

    if st.button("🔄 刷新数据", type="primary", use_container_width=True):
        st.session_state.benchmark_kline = None
        st.session_state.sector_klines = {}
        st.session_state.constituents_data = {}
        st.session_state.rrg_results = {}
        st.session_state.diffusion_results = {}
        st.cache_data.clear()
        st.rerun()


# ── 主区域 ─────────────────────────────────────────────
st.title("📊 板块相对旋转图 + 扩散度分析")

if not st.session_state.selected_sectors:
    st.info("👈 请在侧边栏选择要分析的板块，然后点击「刷新数据」")
    st.stop()

selected_names = st.session_state.selected_sectors
all_sectors = st.session_state.sector_list or []
selected_codes = {}
for s in all_sectors:
    if s["name"] in selected_names:
        selected_codes[s["code"]] = s["name"]

if not selected_codes:
    st.warning("未找到匹配的板块代码")
    st.stop()

# ── 数据加载 ──────────────────────────────────────────
last = st.session_state.last_params
lookback_changed = (lookback != last["lookback"])

data_needs_refresh = (
    st.session_state.benchmark_kline is None
    or len(st.session_state.sector_klines) == 0
    or lookback_changed
)

if lookback_changed:
    # 回看期变了 → 清掉旧 K 线缓存，重新拉
    st.session_state.benchmark_kline = None
    st.session_state.sector_klines = {}
    st.session_state.constituents_data = {}

if data_needs_refresh:
    progress = st.progress(0, text="正在加载基准数据...")

    # 基准 K 线
    try:
        st.session_state.benchmark_kline = fetch_benchmark_kline(lookback)
    except Exception as e:
        st.error(f"基准数据加载失败: {e}")
        st.stop()

    # 板块 K 线（增量加载）
    codes_to_fetch = [c for c in selected_codes if c not in st.session_state.sector_klines]
    if codes_to_fetch:
        progress.progress(20, text=f"正在加载 {len(codes_to_fetch)} 个板块 K 线...")
        new_klines = fetch_sector_klines(codes_to_fetch, lookback)
        st.session_state.sector_klines.update(new_klines)

    # 成分股数据（增量加载）
    codes_to_fetch_const = [c for c in selected_codes
                             if c not in st.session_state.constituents_data]
    for i, code in enumerate(codes_to_fetch_const):
        pct = 30 + int(60 * (i + 1) / max(len(codes_to_fetch_const), 1))
        progress.progress(pct, text=f"加载成分股 [{i+1}/{len(codes_to_fetch_const)}] {selected_codes[code]}...")
        try:
            st.session_state.constituents_data[code] = fetch_constituents_data(
                code, lookback)
        except Exception:
            st.session_state.constituents_data[code] = {"stocks": [], "klines": {}}

    progress.empty()

# ── 计算引擎 ──────────────────────────────────────────
params_changed = (
    window != last["window"]
    or tail != last["tail"]
    or diffusion_ma != last["diffusion_ma"]
)

needs_recalc = (
    not st.session_state.rrg_results
    or not st.session_state.diffusion_results
    or params_changed
    or lookback_changed
)

if needs_recalc:
    with st.spinner("正在计算 RRG 和扩散度..."):
        benchmark = st.session_state.benchmark_kline

        # RRG 计算
        st.session_state.rrg_results = {}
        for code, name in selected_codes.items():
            sector_kline = st.session_state.sector_klines.get(code)
            if sector_kline is None or sector_kline.empty:
                continue
            try:
                st.session_state.rrg_results[name] = compute_rrg(
                    sector_kline, benchmark, window=window, tail=tail)
            except ValueError:
                continue

        # 扩散度计算
        st.session_state.diffusion_results = {}
        for code, name in selected_codes.items():
            cdata = st.session_state.constituents_data.get(code)
            if cdata is None:
                continue
            result = compute_diffusion(cdata, ma_period=diffusion_ma)
            if result["dates"]:
                st.session_state.diffusion_results[name] = result

    # 记录当前参数，下次 rerun 时对比检测变化
    st.session_state.last_params = {
        "window": window,
        "tail": tail,
        "lookback": lookback,
        "diffusion_ma": diffusion_ma,
    }


# ── 图表渲染 ──────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    if st.session_state.rrg_results:
        fig_rrg = build_rrg_chart(st.session_state.rrg_results, tail=tail)
        st.plotly_chart(fig_rrg, use_container_width=True, key="rrg_chart")
    else:
        st.warning("无 RRG 数据可显示")

with col_right:
    if st.session_state.diffusion_results:
        fig_diff = build_diffusion_chart(
            st.session_state.diffusion_results, lookback_days=lookback)
        st.plotly_chart(fig_diff, use_container_width=True, key="diffusion_chart")
    else:
        st.warning("无扩散度数据可显示")


# ── 排行表格 ──────────────────────────────────────────
st.divider()
if st.session_state.sector_list:
    df = build_ranking_table(
        all_sectors,
        st.session_state.rrg_results,
        st.session_state.diffusion_results,
    )
    # 只显示已选板块
    df_filtered = df[df["板块"].isin(selected_names)]
    render_ranking_table(df_filtered, key="ranking_main")
