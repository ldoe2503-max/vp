"""Build, sign and broadcast TON transfers.

The private key stays local: tonsdk signs the transfer message in-process.
toncenter is only used to fetch the account's current seqno (needed to build
a valid transaction) and to submit the already-signed BOC.
"""
import base64
import requests
from tonsdk.contract.wallet import Wallets, WalletVersionEnum

TONCENTER_URL = "https://toncenter.com/api/v2"


def _get_seqno(address: str) -> int:
    resp = requests.get(
        f"{TONCENTER_URL}/runGetMethod",
        params={"address": address, "method": "seqno", "stack": "[]"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        return 0  # freshly created / never-used wallet: seqno starts at 0
    stack = data["result"]["stack"]
    return int(stack[0][1], 16)


def send_ton(mnemonic_phrase: str, to_address: str, amount_ton: float) -> str:
    """Sends TON. Returns the sent BOC hash (transaction identifier)."""
    words = mnemonic_phrase.split()
    _, _, _, wallet = Wallets.from_mnemonics(words, WalletVersionEnum.v4r2, 0)

    from_address = wallet.address.to_string(True, True, True)
    seqno = _get_seqno(from_address)

    query = wallet.create_transfer_message(
        to_addr=to_address,
        amount=int(amount_ton * 1_000_000_000),
        seqno=seqno,
    )
    boc = query["message"].to_boc(False)
    boc_b64 = base64.b64encode(boc).decode()

    resp = requests.post(
        f"{TONCENTER_URL}/sendBoc", json={"boc": boc_b64}, timeout=15
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("error", "toncenter broadcast error"))
    return data["result"].get("hash", "sent")
