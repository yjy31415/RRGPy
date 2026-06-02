"""扩散度时序图 — Plotly 多折线实现。"""
from __future__ import annotations

import plotly.graph_objects as go


# 趋势灯色带
LIGHT_COLORS = {
    "expansion":   "rgba(46,204,64,0.15)",
    "contraction": "rgba(255,65,54,0.15)",
    "neutral":     "rgba(255,220,0,0.08)",
    "unknown":     "rgba(200,200,200,0.05)",
}


def build_diffusion_chart(
    diffusion_results: dict[str, dict],
    lookback_days: int = 60,
) -> go.Figure:
    """构建扩散度多板块对比时序图。

    Args:
        diffusion_results: {sector_name: {dates, smoothed_diffusion, trend_light}}
        lookback_days: x 轴显示天数

    Returns:
        Plotly Figure 对象
    """
    fig = go.Figure()

    # 色带区域（取第一个板块的趋势灯做参考色带）
    if diffusion_results:
        first_name = list(diffusion_results.keys())[0]
        first_data = diffusion_results[first_name]
        dates = first_data["dates"]
        lights = first_data["trend_light"]

        if dates and lights:
            # 按连续相同趋势灯分段绘制色带
            segments = []
            current_light = lights[0]
            seg_start = 0
            for i in range(1, len(lights)):
                if lights[i] != current_light:
                    segments.append((seg_start, i - 1, current_light))
                    seg_start = i
                    current_light = lights[i]
            segments.append((seg_start, len(lights) - 1, current_light))

            for start, end, light in segments:
                if start < len(dates) and end < len(dates):
                    fig.add_vrect(
                        x0=dates[start], x1=dates[end],
                        fillcolor=LIGHT_COLORS.get(light, LIGHT_COLORS["unknown"]),
                        layer="below", line_width=0,
                    )

    # 各板块扩散度折线
    color_palette = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]
    for i, (name, result) in enumerate(diffusion_results.items()):
        color = color_palette[i % len(color_palette)]
        smoothed = result.get("smoothed_diffusion", [])
        dates = result.get("dates", [])

        if not dates or not smoothed:
            continue

        # 裁剪到 lookback_days
        if len(dates) > lookback_days:
            dates = dates[-lookback_days:]
            smoothed = smoothed[-lookback_days:]

        fig.add_trace(go.Scatter(
            x=dates, y=smoothed,
            mode="lines",
            name=name,
            line=dict(color=color, width=2),
            hovertemplate=(
                f"<b>{name}</b><br>"
                "日期: %{x|%Y-%m-%d}<br>"
                "扩散度: %{y:.1f}%<extra></extra>"
            ),
        ))

    # 参考线
    fig.add_hline(y=60, line=dict(color="green", width=1, dash="dot"),
                  annotation_text="扩张", annotation_position="right")
    fig.add_hline(y=40, line=dict(color="red", width=1, dash="dot"),
                  annotation_text="收缩", annotation_position="right")
    fig.add_hline(y=50, line=dict(color="grey", width=1, dash="dash"),
                  annotation_text="均衡")

    fig.update_xaxes(title="日期", rangeslider=dict(visible=True))
    fig.update_yaxes(title="扩散度 (%)", range=[0, 105])

    fig.update_layout(
        title="板块扩散度 (市值加权 | MA20 平滑)",
        height=600,
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=60, r=60, t=50, b=50),
        hovermode="x unified",
    )

    return fig
