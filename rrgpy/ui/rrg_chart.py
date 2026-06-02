"""RRG 四象限散点图 — Plotly 实现。"""
from __future__ import annotations

import plotly.graph_objects as go


# 象限配色
QUADRANT_COLORS = {
    "leading":   "#2ECC40",  # 绿
    "weakening": "#FFDC00",  # 黄
    "lagging":   "#FF4136",  # 红
    "improving": "#0074D9",  # 蓝
    "unknown":   "#AAAAAA",  # 灰
}


def build_rrg_chart(
    rrg_results: dict[str, dict],
    tail: int = 5,
) -> go.Figure:
    """构建 RRG 四象限 Plotly 图表。

    Args:
        rrg_results: {sector_name: {dates, rs_ratio, rs_momentum, quadrant}}
        tail: 轨迹尾巴点数

    Returns:
        Plotly Figure 对象
    """
    fig = go.Figure()

    # 四象限背景
    # Leading (右上)
    fig.add_shape(type="rect", x0=100, x1=110, y0=101, y1=110,
                  fillcolor="rgba(46,204,64,0.08)",
                  line=dict(width=0), layer="below")
    # Improving (左上)
    fig.add_shape(type="rect", x0=90, x1=100, y0=101, y1=110,
                  fillcolor="rgba(0,116,217,0.08)",
                  line=dict(width=0), layer="below")
    # Lagging (左下)
    fig.add_shape(type="rect", x0=90, x1=100, y0=90, y1=101,
                  fillcolor="rgba(255,65,54,0.08)",
                  line=dict(width=0), layer="below")
    # Weakening (右下)
    fig.add_shape(type="rect", x0=100, x1=110, y0=90, y1=101,
                  fillcolor="rgba(255,220,0,0.08)",
                  line=dict(width=0), layer="below")

    # 原点十字线
    fig.add_hline(y=101, line=dict(color="grey", width=1, dash="dash"))
    fig.add_vline(x=100, line=dict(color="grey", width=1, dash="dash"))

    # 象限标签
    fig.add_annotation(x=95, y=108, text="Improving", showarrow=False,
                       font=dict(size=10, color="#0074D9"))
    fig.add_annotation(x=108, y=108, text="Leading", showarrow=False,
                       font=dict(size=10, color="#2ECC40"))
    fig.add_annotation(x=108, y=95, text="Weakening", showarrow=False,
                       font=dict(size=10, color="#CCAA00"))
    fig.add_annotation(x=95, y=95, text="Lagging", showarrow=False,
                       font=dict(size=10, color="#CC3333"))

    # 画每个板块
    for name, result in rrg_results.items():
        rr = result["rs_ratio"]
        rm = result["rs_momentum"]
        quads = result["quadrant"]

        if len(rr) < 2:
            continue

        # 取 tail 长度
        trail_rr = rr[-tail:] if len(rr) >= tail else rr
        trail_rm = rm[-tail:] if len(rm) >= tail else rm
        quadrant = quads[-1] if quads else "unknown"
        color = QUADRANT_COLORS.get(quadrant, "#AAAAAA")

        # 轨迹线
        fig.add_trace(go.Scatter(
            x=trail_rr, y=trail_rm,
            mode="lines",
            line=dict(color="grey", width=1),
            showlegend=False,
            hoverinfo="skip",
        ))

        # 尾巴历史点（小点）+ 末端大点
        sizes = [8] * (len(trail_rr) - 1) + [16]
        colors_trail = ["lightgrey"] * (len(trail_rr) - 1) + [color]
        fig.add_trace(go.Scatter(
            x=trail_rr, y=trail_rm,
            mode="markers",
            marker=dict(size=sizes, color=colors_trail),
            showlegend=False,
            hoverinfo="skip",
        ))

        # 板块名标签
        fig.add_annotation(
            x=trail_rr[-1], y=trail_rm[-1],
            text=name,
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1,
            arrowcolor=color,
            font=dict(size=11, color=color),
            ax=10, ay=-10,
        )

    # 坐标轴
    fig.update_xaxes(
        title="RS-Ratio (JdK)",
        range=[90, 110],
        zeroline=False,
    )
    fig.update_yaxes(
        title="RS-Momentum (JdK)",
        range=[90, 110],
        zeroline=False,
    )

    fig.update_layout(
        title="板块相对旋转图 (RRG)",
        height=600,
        plot_bgcolor="white",
        showlegend=False,
        margin=dict(l=60, r=60, t=50, b=50),
    )

    return fig
