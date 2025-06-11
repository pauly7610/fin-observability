from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
import os
from apps.backend import vault_utils

PRIVATE_KEY_PATH = os.getenv("EXPORT_SIGNING_KEY", "private_key.pem")


# Load private key from vault or PEM file
def load_private_key():
    use_vault = os.getenv("USE_VAULT_FOR_SIGNING_KEY", "false").lower() == "true"
    if use_vault:
        key_bytes = vault_utils.get_private_key_from_vault()
        return load_pem_private_key(key_bytes, password=None, backend=default_backend())
    else:
        with open(PRIVATE_KEY_PATH, "rb") as key_file:
            return load_pem_private_key(
                key_file.read(), password=None, backend=default_backend()
            )


def sign_data(data: bytes) -> bytes:
    private_key = load_private_key()
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    return signature


def write_signature_file(filename: str, signature: bytes):
    sigfile = filename + ".sig"
    with open(sigfile, "wb") as f:
        f.write(signature)
