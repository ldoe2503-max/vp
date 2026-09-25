"""Real currency exchange via ChangeNOW's non-custodial swap API.

How this stays non-custodial: this app never touches the other side of the
trade. It asks ChangeNOW for a quote and a one-time deposit address, you (or
this app, using your own key) send YOUR coins from YOUR wallet to that
deposit address, and ChangeNOW sends the converted coins to the destination
address you specify -- which should be your own address on the other chain.
Nobody but ChangeNOW ever custodies funds mid-swap, and this app never
custodies them at all.

Needs a free API key from https://changenow.io/affiliate (or their partner
API dashboard) -- put it in your vault as `changenow_api_key` or pass it in.
"""
import requests

BASE_URL = "https://api.changenow.io/v2"

# ChangeNOW ticker + network codes for the assets this wallet supports
TICKERS = {
    "xmr": ("xmr", None),
    "ton": ("ton", None),
    "usdt_trc20": ("usdt", "trx"),
}


def get_estimate(api_key: str, from_asset: str, to_asset: str, amount: float) -> dict:
    """from_asset/to_asset are keys of TICKERS, e.g. 'xmr', 'usdt_trc20'."""
    from_ticker, from_network = TICKERS[from_asset]
    to_ticker, to_network = TICKERS[to_asset]

    params = {
        "fromCurrency": from_ticker,
        "toCurrency": to_ticker,
        "fromAmount": amount,
        "flow": "standard",
    }
    if from_network:
        params["fromNetwork"] = from_network
    if to_network:
        params["toNetwork"] = to_network

    resp = requests.get(
        f"{BASE_URL}/exchange/estimated-amount",
        params=params,
        headers={"x-changenow-api-key": api_key},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def create_exchange(
    api_key: str,
    from_asset: str,
    to_asset: str,
    amount: float,
    to_address: str,
    refund_address: str,
) -> dict:
    """Creates the swap order. Returns dict including `payinAddress` -- send
    `amount` of `from_asset` there from your own wallet to execute the swap.
    """
    from_ticker, from_network = TICKERS[from_asset]
    to_ticker, to_network = TICKERS[to_asset]

    body = {
        "fromCurrency": from_ticker,
        "toCurrency": to_ticker,
        "fromAmount": amount,
        "address": to_address,
        "refundAddress": refund_address,
        "flow": "standard",
    }
    if from_network:
        body["fromNetwork"] = from_network
    if to_network:
        body["toNetwork"] = to_network

    resp = requests.post(
        f"{BASE_URL}/exchange",
        json=body,
        headers={"x-changenow-api-key": api_key},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def get_status(api_key: str, exchange_id: str) -> dict:
    resp = requests.get(
        f"{BASE_URL}/exchange/by-id",
        params={"id": exchange_id},
        headers={"x-changenow-api-key": api_key},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()
