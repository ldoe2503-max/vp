"""Read-only balance checks via public block explorer / node APIs.

Nothing here ever sends a private key or spend key over the network.
"""
import requests

TRONGRID_URL = "https://api.trongrid.io"
TONCENTER_URL = "https://toncenter.com/api/v2"

# Public light-wallet server implementing the MyMonero/OpenMonero protocol.
# Only the *view key* + address are sent (never the spend key), which lets
# the server compute your balance/history without being able to spend your
# funds -- but it does learn your incoming transactions. For full privacy,
# run your own `monero-wallet-rpc` against a node you trust instead; this
# app's `restore()` output gives you everything needed to do that.
XMR_LIGHT_WALLET_URL = "https://api.mymonero.com:8443"

USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"


def tron_balance(address: str) -> dict:
    """Returns {"TRX": <float>, "USDT": <float>} for a Tron address."""
    url = f"{TRONGRID_URL}/v1/accounts/{address}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    result = {"TRX": 0.0, "USDT": 0.0}
    accounts = data.get("data", [])
    if not accounts:
        return result  # unused/empty account: zero balance

    acct = accounts[0]
    result["TRX"] = acct.get("balance", 0) / 1_000_000

    for token in acct.get("trc20", []):
        if USDT_TRC20_CONTRACT in token:
            raw = int(token[USDT_TRC20_CONTRACT])
            result["USDT"] = raw / 1_000_000  # USDT-TRC20 has 6 decimals
    return result


def ton_balance(address: str) -> float:
    """Returns TON balance as a float."""
    url = f"{TONCENTER_URL}/getAddressBalance"
    resp = requests.get(url, params={"address": address}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("error", "toncenter error"))
    nanotons = int(data["result"])
    return nanotons / 1_000_000_000


def xmr_balance(address: str, view_key: str) -> dict:
    """Returns {"total": <float>, "unlocked": <float>} in XMR.

    Uses a MyMonero-protocol light-wallet server: only address + view key
    are sent, the spend key never leaves this machine.
    """
    url = f"{XMR_LIGHT_WALLET_URL}/get_address_info"
    payload = {"address": address, "view_key": view_key}
    resp = requests.post(url, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    total = int(data.get("total_received", 0)) - int(data.get("total_sent", 0))
    locked = int(data.get("locked_funds", 0))
    return {
        "total": total / 1e12,
        "unlocked": (total - locked) / 1e12,
    }
