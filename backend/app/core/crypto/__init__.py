"""Zentrale Crypto-Fassade – ein Einstiegspunkt für alle Verschlüsselungsoperationen."""

from app.core.crypto.classification import DataClassification, classification_label
from app.core.crypto.classification_catalog import CLASSIFICATION_CATALOG, get_policy
from app.core.crypto.field_registry import field_classification
from app.core.crypto.encryption import (
    CryptoError,
    decrypt,
    decrypt_text,
    decrypt_text_master,
    decrypt_with_master_key,
    encrypt,
    encrypt_text,
    encrypt_text_master,
    encrypt_with_master_key,
    generate_master_key_b64,
)
from app.core.crypto.key_derivation import derive_user_key, generate_salt

__all__ = [
    "CLASSIFICATION_CATALOG",
    "CryptoError",
    "DataClassification",
    "classification_label",
    "field_classification",
    "get_policy",
    "decrypt",
    "decrypt_text",
    "decrypt_text_master",
    "decrypt_with_master_key",
    "derive_user_key",
    "encrypt",
    "encrypt_text",
    "encrypt_text_master",
    "encrypt_with_master_key",
    "generate_master_key_b64",
    "generate_salt",
]
