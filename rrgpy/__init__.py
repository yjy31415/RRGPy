"""rrgpy — A股板块 RRG + 扩散度分析系统。"""

# 必须在初始化任何 requests 前禁用 IPv6
# push2.eastmoney.com 的 IPv6 地址 (240e:e1:8000:1b04::25d) 被 CDN/WAF 拦截
import urllib3.util.connection
urllib3.util.connection.HAS_IPV6 = False
