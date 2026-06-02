"""板块排行表格 — Streamlit DataFrame。"""
from __future__ import annotations

import pandas as pd
import streamlit as st


def build_ranking_table(
    sector_list: list[dict],
    rrg_results: dict[str, dict],
    diffusion_results: dict[str, dict],
) -> pd.DataFrame:
    """构建板块排行 DataFrame。

    Args:
        sector_list: fetch_sector_list() 返回值
        rrg_results: {sector_name: {rs_ratio, rs_momentum, quadrant}}
        diffusion_results: {sector_name: {smoothed_diffusion, trend_light}}

    Returns:
        排好序的 DataFrame
    """
    rows = []
    for sector in sector_list:
        name = sector["name"]
        code = sector["code"]

        row = {
            "板块": name,
            "代码": code,
            "涨跌幅%": sector.get("change_pct", 0),
            "RS-Ratio": None,
            "RS-Momentum": None,
            "象限": "-",
            "扩散度%": None,
            "趋势": "-",
        }

        # 合并 RRG 结果
        if name in rrg_results:
            rrg = rrg_results[name]
            if rrg["rs_ratio"]:
                row["RS-Ratio"] = round(rrg["rs_ratio"][-1], 2)
                row["RS-Momentum"] = round(rrg["rs_momentum"][-1], 2)
            quadrant = rrg.get("quadrant", ["unknown"])[-1]
            quadrant_cn = {
                "leading": "🟢 领先",
                "improving": "🔵 改善",
                "lagging": "🔴 滞后",
                "weakening": "🟡 走弱",
            }.get(quadrant, quadrant)
            row["象限"] = quadrant_cn

        # 合并扩散度结果
        if name in diffusion_results:
            diff = diffusion_results[name]
            smoothed = diff.get("smoothed_diffusion", [])
            if smoothed and smoothed[-1] is not None:
                row["扩散度%"] = round(smoothed[-1], 1)
            light = diff.get("trend_light", ["unknown"])[-1]
            light_cn = {
                "expansion": "🟢 扩张",
                "contraction": "🔴 收缩",
                "neutral": "🟡 中性",
            }.get(light, "-")
            row["趋势"] = light_cn

        rows.append(row)

    df = pd.DataFrame(rows)
    # 默认按涨跌幅降序
    df = df.sort_values("涨跌幅%", ascending=False)
    return df


def render_ranking_table(df: pd.DataFrame, key: str = "ranking") -> None:
    """在 Streamlit 中渲染可排序、可点击高亮的表格。

    使用 st.dataframe 或 st.data_editor 实现行选择。
    """
    selection = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "涨跌幅%": st.column_config.NumberColumn(format="%.2f"),
            "RS-Ratio": st.column_config.NumberColumn(format="%.2f"),
            "RS-Momentum": st.column_config.NumberColumn(format="%.2f"),
            "扩散度%": st.column_config.NumberColumn(format="%.1f"),
        },
        key=key,
        on_select="rerun",
        selection_mode="multi-row",
    )
    return selection
