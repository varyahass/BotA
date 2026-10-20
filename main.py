# Шаг 0: диагностическая проверка доступа к API бирж с сервера Railway.
# Программа 3 раза (раз в минуту) запрашивает Kraken и Coinbase Exchange
# и печатает в лог: HTTP-статус, время ожидания, bid, ask и объёмы.
# Ничего не торгует, ключи бирж не нужны.

import time
from datetime import datetime, timezone

import requests

KRAKEN_URL = "https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=1"
COINBASE_URL = "https://api.exchange.coinbase.com/products/BTC-USD/book?level=1"
HEADERS = {"User-Agent": "arbitrage-research-bot-A/0.1"}


def check_numbers(name, bid_p, bid_v, ask_p, ask_v):
    problems = []
    for label, value in [("bid", bid_p), ("объём bid", bid_v), ("ask", ask_p), ("объём ask", ask_v)]:
        if value <= 0:
            problems.append(f"{label} не положителен ({value})")
    if bid_p > ask_p:
        problems.append(f"bid ({bid_p}) больше ask ({ask_p})")
    if problems:
        print(f"  [{name}] ПРОБЛЕМА: " + "; ".join(problems), flush=True)
    else:
        print(f"  [{name}] OK: числа положительные, bid <= ask", flush=True)


def check_kraken():
    t0 = time.time()
    r = requests.get(KRAKEN_URL, headers=HEADERS, timeout=10)
    wait = time.time() - t0
    print(f"Kraken: HTTP {r.status_code}, ожидание {wait:.2f} с", flush=True)
    if r.status_code != 200:
        print("  Текст ответа:", r.text[:300], flush=True)
        return
    data = r.json()
    if data.get("error"):
        print("  Kraken вернул ошибку:", data["error"], flush=True)
        return
    result = data["result"]
    pair_key = list(result.keys())[0]  # обычно 'XXBTZUSD'
    book = result[pair_key]
    bid_p, bid_v = float(book["bids"][0][0]), float(book["bids"][0][1])
    ask_p, ask_v = float(book["asks"][0][0]), float(book["asks"][0][1])
    print(f"  пара в ответе: {pair_key}", flush=True)
    print(f"  bid = {bid_p} USD, объём {bid_v} BTC", flush=True)
    print(f"  ask = {ask_p} USD, объём {ask_v} BTC", flush=True)
    check_numbers("Kraken", bid_p, bid_v, ask_p, ask_v)


def check_coinbase():
    t0 = time.time()
    r = requests.get(COINBASE_URL, headers=HEADERS, timeout=10)
    wait = time.time() - t0
    print(f"Coinbase: HTTP {r.status_code}, ожидание {wait:.2f} с", flush=True)
    if r.status_code != 200:
        print("  Текст ответа:", r.text[:300], flush=True)
        return
    data = r.json()
    bid_p, bid_v = float(data["bids"][0][0]), float(data["bids"][0][1])
    ask_p, ask_v = float(data["asks"][0][0]), float(data["asks"][0][1])
    print(f"  bid = {bid_p} USD, объём {bid_v} BTC", flush=True)
    print(f"  ask = {ask_p} USD, объём {ask_v} BTC", flush=True)
    check_numbers("Coinbase", bid_p, bid_v, ask_p, ask_v)


for attempt in range(1, 4):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"\n===== Проверка {attempt} из 3, {now} =====", flush=True)
    for check in (check_kraken, check_coinbase):
        try:
            check()
        except Exception as e:
            print(f"  ОШИБКА в {check.__name__}: {type(e).__name__}: {e}", flush=True)
    if attempt < 3:
        time.sleep(60)

print("\nДиагностика завершена.", flush=True)
