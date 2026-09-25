"""USDT on TRON (TRC20) key generation and address derivation. Fully offline.

USDT itself is a token contract on Tron; the wallet is a plain Tron account
(TRX address) that can hold both TRX (for fees) and the USDT-TRC20 token.
"""
from bip_utils import (
    Bip39SeedGenerator,
    Bip39MnemonicGenerator,
    Bip39MnemonicValidator,
    Bip44,
    Bip44Coins,
)

USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # canonical USDT-TRC20 contract


def generate() -> dict:
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(24)
    return _describe(str(mnemonic))


def restore(mnemonic_phrase: str) -> dict:
    if not Bip39MnemonicValidator().IsValid(mnemonic_phrase):
        raise ValueError("Некорректная BIP39-мнемоника")
    return _describe(mnemonic_phrase)


def _describe(mnemonic_phrase: str) -> dict:
    seed_bytes = Bip39SeedGenerator(mnemonic_phrase).Generate()
    acct = Bip44.FromSeed(seed_bytes, Bip44Coins.TRON).DeriveDefaultPath()
    return {
        "chain": "usdt_trc20",
        "mnemonic": mnemonic_phrase,
        "address": acct.PublicKey().ToAddress(),
        "private_key": acct.PrivateKey().Raw().ToHex(),
        "usdt_contract": USDT_CONTRACT,
    }
