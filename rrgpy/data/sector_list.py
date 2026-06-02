"""东财行业板块列表获取。"""
from __future__ import annotations

import requests
from rrgpy.config import CLIST_URL, UA, REQUEST_TIMEOUT


def fetch_sector_list() -> list[dict]:
    """拉取东财行业板块列表（~100 个）。

    Returns:
        [{code: "BK0425", name: "电力设备", change_pct: 1.23, ...}, ...]
    """
    params = {
        "pn": "1",
        "pz": "200",
        "po": "1",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fs": "m:90+t:2",
        "fields": "f2,f3,f4,f12,f14,f104,f105,f128",
    }
    headers = {"User-Agent": UA}
    r = requests.get(CLIST_URL, params=params, headers=headers,
                     timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    data = r.json()

    items = data.get("data", {}).get("diff", [])
    if not items:
        return []

    sectors = []
    for i, item in enumerate(items):
        sectors.append({
            "code": item.get("f12", ""),
            "name": item.get("f14", ""),
            "change_pct": item.get("f3", 0),
            "rank": i + 1,
            "up_count": item.get("f104", 0),
            "down_count": item.get("f105", 0),
        })
    return sectors
