import random
import requests
from datetime import datetime, date, timedelta

# {month_str: {date_str: bool}}  e.g. {"2026-05": {"2026-05-01": False, ...}}
_cache: dict = {}


def _fetch_month(month: str) -> bool:
    """拉取指定月份交易日历（month 格式 YYYY-MM），缓存到 _cache。"""
    if _cache.get(month):
        return True
    try:
        url = f"https://www.szse.cn/api/report/exchange/onepersistenthour/monthList?month={month}&random={random.random()}"
        resp = requests.get(url, timeout=10)
        data = resp.json().get("data", [])
        if not data:
            return False
        _cache[month] = {item["jyrq"]: item["jybz"] == "1" for item in data}
        return True
    except Exception:
        return False


def is_trade_day(check_date: str = None) -> bool:
    """判断指定日期是否为交易日（YYYY-MM-DD），网络失败时返回 False。"""
    if check_date is None:
        check_date = datetime.today().strftime("%Y-%m-%d")
    month = check_date[:7]
    if not _fetch_month(month):
        return False
    return _cache[month].get(check_date, False)


def is_today_trade_day() -> bool:
    return is_trade_day(datetime.today().strftime("%Y-%m-%d"))


def next_trade_day(from_date: date) -> date:
    """返回 from_date 之后（不含当天）的第一个交易日，网络失败时最多找 30 天。"""
    d = from_date + timedelta(days=1)
    for _ in range(30):
        if is_trade_day(d.strftime("%Y-%m-%d")):
            return d
        d += timedelta(days=1)
    return d


if __name__ == "__main__":
    today = datetime.today().strftime("%Y-%m-%d")
    print(f"{today} 是否交易日: {is_trade_day(today)}")
