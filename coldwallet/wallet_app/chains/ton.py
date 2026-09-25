"""TON key generation and address derivation. Fully offline.

Uses the official TON mnemonic scheme (not BIP39) and wallet v4r2 contract,
so the resulting seed phrase and address are compatible with Tonkeeper and
the official TON wallet apps.
"""
from tonsdk.crypto import mnemonic_new, mnemonic_is_valid
from tonsdk.contract.wallet import Wallets, WalletVersionEnum


def generate() -> dict:
    mnemonic_words = mnemonic_new(24)
    return _describe(mnemonic_words)


def restore(mnemonic_phrase: str) -> dict:
    words = mnemonic_phrase.split()
    if not mnemonic_is_valid(words):
        raise ValueError("Некорректная TON-мнемоника")
    return _describe(words)


def _describe(mnemonic_words: list) -> dict:
    _, pub_key, priv_key, wallet = Wallets.from_mnemonics(
        mnemonic_words, WalletVersionEnum.v4r2, 0
    )
    return {
        "chain": "ton",
        "mnemonic": " ".join(mnemonic_words),
        "address": wallet.address.to_string(True, True, True),
        "address_non_bounceable": wallet.address.to_string(True, True, False),
        "public_key": pub_key.hex(),
        "private_key": priv_key.hex(),
    }
