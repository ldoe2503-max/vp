"""Live exchange rates via CoinGecko's free public API.

No API key required, read-only, no wallet data is sent anywhere.
"""
import requests

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

# CoinGecko coin ids for the assets this wallet supports
COIN_IDS = {
    "XMR": "monero",
    "TON": "the-open-network",
    "USDT": "tether",
}

VS_CURRENCIES = ["usd", "rub"]


def get_rates() -> dict:
    """Returns {"XMR": {"usd": ..., "rub": ...}, "TON": {...}, "USDT": {...}}."""
    params = {
        "ids": ",".join(COIN_IDS.values()),
        "vs_currencies": ",".join(VS_CURRENCIES),
    }
    resp = requests.get(COINGECKO_URL, params=params, timeout=15)
    resp.raise_for_status()
    raw = resp.json()

    result = {}
    for symbol, coin_id in COIN_IDS.items():
        if coin_id in raw:
            result[symbol] = raw[coin_id]
    return result


def format_rates_table(rates: dict) -> str:
    lines = [f"{'Монета':<8}{'USD':>12}{'RUB':>14}"]
    lines.append("-" * 34)
    for symbol, values in rates.items():
        usd = values.get("usd", "?")
        rub = values.get("rub", "?")
        lines.append(f"{symbol:<8}{usd:>12}{rub:>14}")
    return "\n".join(lines)
