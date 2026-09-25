"""Encrypted local vault for wallet secrets.

Everything here stays on disk, on this machine, encrypted at rest.
Nothing in this module makes a network call.
"""
import json
import os
import secrets
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

VAULT_DIR = Path.home() / ".coldwallet"
VAULT_FILE = VAULT_DIR / "vault.dat"

SCRYPT_N = 2 ** 17
SCRYPT_R = 8
SCRYPT_P = 1
KEY_LEN = 32
SALT_LEN = 16
NONCE_LEN = 12

MAGIC = b"CWV1"


class VaultError(Exception):
    pass


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=KEY_LEN, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return kdf.derive(password.encode("utf-8"))


def vault_exists() -> bool:
    return VAULT_FILE.exists()


def create_vault(password: str, data: dict) -> None:
    """Encrypt `data` (a plain dict of wallet secrets) and write the vault file.

    Overwrites any existing vault -- caller must confirm with the user first.
    """
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    salt = secrets.token_bytes(SALT_LEN)
    key = _derive_key(password, salt)
    nonce = secrets.token_bytes(NONCE_LEN)
    plaintext = json.dumps(data).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated_data=MAGIC)

    blob = MAGIC + salt + nonce + ciphertext
    tmp = VAULT_FILE.with_suffix(".tmp")
    tmp.write_bytes(blob)
    os.chmod(tmp, 0o600)
    tmp.replace(VAULT_FILE)


def load_vault(password: str) -> dict:
    if not VAULT_FILE.exists():
        raise VaultError("Хранилище не найдено. Сначала создайте кошелёк (пункт 1).")

    blob = VAULT_FILE.read_bytes()
    magic, rest = blob[:4], blob[4:]
    if magic != MAGIC:
        raise VaultError("Файл хранилища повреждён или это не тот формат.")

    salt, rest = rest[:SALT_LEN], rest[SALT_LEN:]
    nonce, ciphertext = rest[:NONCE_LEN], rest[NONCE_LEN:]

    key = _derive_key(password, salt)
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, associated_data=MAGIC)
    except Exception:
        raise VaultError("Неверный пароль или файл повреждён.")

    return json.loads(plaintext.decode("utf-8"))


def update_vault(password: str, data: dict) -> None:
    """Re-encrypt updated data with a fresh salt/nonce."""
    create_vault(password, data)
