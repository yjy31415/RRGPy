"""全局配置常量。"""

# 基准
BENCHMARK_CODE = "830000"
BENCHMARK_SECID = "1.830000"  # 上交所指数
BENCHMARK_NAME = "A股平均股价"

# RRG 参数
WINDOW = 10          # 滚动窗口 (日)
TAIL = 5             # 轨迹尾巴点数
LOOKBACK = 60        # 回看期 (日)

# 扩散度参数
DIFFUSION_MA = 20           # MA 平滑周期
EXPANSION_THRESHOLD = 60    # 扩张阈值
CONTRACTION_THRESHOLD = 40  # 收缩阈值

# 东财 push2 API
PUSH2_BASE = "https://push2.eastmoney.com/api/qt"
PUSH2HIS_BASE = "https://push2his.eastmoney.com/api/qt"
CLIST_URL = f"{PUSH2_BASE}/clist/get"
STOCK_URL = f"{PUSH2_BASE}/stock/get"
KLIN_URL = f"{PUSH2HIS_BASE}/stock/kline/get"

# 请求控制
REQUEST_TIMEOUT = 15        # 请求超时 (秒)
RETRY_COUNT = 1             # 重试次数
RETRY_DELAY = 1.5           # 重试间隔 (秒)
BATCH_SIZE = 20             # 并发请求数

# 缓存
CACHE_DIR = ".rrgpy_cache"

# 通用 UA
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/117.0.0.0 Safari/537.36")
