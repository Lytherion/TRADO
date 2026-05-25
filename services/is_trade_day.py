import requests
from datetime import datetime, date, timedelta

_trade_dates: set = set()
_fetched = False


def _fetch_trade_dates() -> bool:
    """从腾讯金融 API 拉取最近 100 个交易日，缓存到 _trade_dates。"""
    global _fetched
    if _fetched:
        return True
    try:
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000001,day,,,100,"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        kline = data["data"]["sh000001"]["day"]
        _trade_dates.update(item[0] for item in kline)
        _fetched = True
        return True
    except Exception:
        return False


def is_trade_day(check_date: str = None) -> bool:
    """判断指定日期是否为交易日（YYYY-MM-DD），网络失败时返回 False。"""
    if check_date is None:
        check_date = datetime.today().strftime("%Y-%m-%d")

    if check_date in _trade_dates:
        return True

    if not _fetch_trade_dates():
        return False

    return check_date in _trade_dates


def is_today_trade_day() -> bool:
    return is_trade_day(datetime.today().strftime("%Y-%m-%d"))


def next_trade_day(from_date: date) -> date:
    """返回 from_date 之后（不含当天）的第一个交易日，网络失败时最多找 30 天。"""
    _fetch_trade_dates()
    d = from_date + timedelta(days=1)
    for _ in range(30):
        if is_trade_day(d.strftime("%Y-%m-%d")):
            return d
        d += timedelta(days=1)
    return d  # 兜底


if __name__ == "__main__":
    today = datetime.today().strftime("%Y-%m-%d")
    print(f"{today} 是否交易日: {is_trade_day(today)}")
