"""Build, sign and broadcast TRX / USDT-TRC20 transfers.

The private key is only ever used locally, inside PrivateKey.sign(); it is
never sent to TronGrid or anywhere else. TronGrid is only used to fetch
current chain state (needed to build a valid transaction) and to broadcast
the already-signed transaction.
"""
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"


def _client() -> Tron:
    return Tron(HTTPProvider("https://api.trongrid.io"))


def send_trx(private_key_hex: str, to_address: str, amount_trx: float) -> str:
    """Sends native TRX. Returns the broadcast transaction id."""
    client = _client()
    priv = PrivateKey(bytes.fromhex(private_key_hex))
    from_address = priv.public_key.to_base58check_address()

    txn = (
        client.trx.transfer(from_address, to_address, int(amount_trx * 1_000_000))
        .build()
        .sign(priv)
    )
    result = txn.broadcast()
    return result["txid"]


def send_usdt(private_key_hex: str, to_address: str, amount_usdt: float) -> str:
    """Sends USDT-TRC20. Returns the broadcast transaction id."""
    client = _client()
    priv = PrivateKey(bytes.fromhex(private_key_hex))
    from_address = priv.public_key.to_base58check_address()

    contract = client.get_contract(USDT_CONTRACT)
    txn = (
        contract.functions.transfer(to_address, int(amount_usdt * 1_000_000))
        .with_owner(from_address)
        .fee_limit(20_000_000)
        .build()
        .sign(priv)
    )
    result = txn.broadcast()
    return result["txid"]
