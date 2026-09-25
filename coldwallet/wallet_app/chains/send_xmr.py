"""Monero transfers via a locally-run monero-wallet-rpc process.

Why this is different from TRON/TON: building a valid Monero transaction
(ring signatures, decoy selection, correct fee) is genuinely unsafe to
reimplement from scratch -- a bug can permanently lock or destroy funds, or
break the privacy guarantees Monero exists for. Every serious Monero wallet
(including the official GUI) relies on the Monero project's own
`monero-wallet-rpc` binary to do this. This module therefore talks to that
process over JSON-RPC on 127.0.0.1 -- it never leaves your machine, and you
are always the one who started it with your own restored wallet file.

Setup (one-time, documented in SETUP.md):
  1. Download the official Monero CLI bundle from getmonero.org.
  2. Restore your wallet file from the mnemonic this app generated, using
     `monero-wallet-cli --restore-deterministic-wallet`.
  3. Run:
     monero-wallet-rpc --wallet-file mywallet --password "" \
         --rpc-bind-port 18082 --daemon-address <a remote node> \
         --disable-rpc-login
  4. Leave that process running while you use this app's Monero features.
"""
import requests

RPC_URL = "http://127.0.0.1:18082/json_rpc"


def _call(method: str, params: dict | None = None) -> dict:
    payload = {"jsonrpc": "2.0", "id": "0", "method": method, "params": params or {}}
    resp = requests.post(RPC_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("message", "monero-wallet-rpc error"))
    return data["result"]


def is_rpc_available() -> bool:
    try:
        _call("get_version")
        return True
    except Exception:
        return False


def get_balance() -> dict:
    result = _call("get_balance")
    return {
        "total": result["balance"] / 1e12,
        "unlocked": result["unlocked_balance"] / 1e12,
    }


def send_xmr(to_address: str, amount_xmr: float) -> str:
    """Sends XMR via the local wallet-rpc. Returns the transaction hash."""
    params = {
        "destinations": [{"amount": int(amount_xmr * 1e12), "address": to_address}],
        "priority": 1,
        "get_tx_key": True,
    }
    result = _call("transfer", params)
    return result["tx_hash"]
