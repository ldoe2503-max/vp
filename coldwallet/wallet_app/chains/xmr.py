"""Monero (XMR) key generation and address derivation. Fully offline."""
from monero.seed import Seed
from monero import const


def generate() -> dict:
    seed = Seed()
    return _describe(seed)


def restore(mnemonic_phrase: str) -> dict:
    seed = Seed(mnemonic_phrase)
    return _describe(seed)


def _describe(seed: Seed) -> dict:
    return {
        "chain": "monero",
        "mnemonic": seed.phrase,
        "address": str(seed.public_address(net=const.NET_MAIN)),
        "spend_key": seed.secret_spend_key(),
        "view_key": seed.secret_view_key(),
    }
