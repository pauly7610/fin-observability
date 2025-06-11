import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
import sys
import os


def verify_hash_chain(csv_file):
    with open(csv_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(csv_file + ".hash", "r", encoding="utf-8") as hfile:
        hashes = [h.strip() for h in hfile.readlines()]
    prev_hash = ""
    for i, line in enumerate(lines):
        data = (prev_hash + line).encode()
        h = hashlib.sha256(data).hexdigest()
        if h != hashes[i]:
            print(f"Hash mismatch at line {i+1}")
            return False
        prev_hash = h
    print("Hash chain verified.")
    return True


def verify_signature(csv_file, pubkey_path=None):
    if pubkey_path is None:
        pubkey_path = os.getenv("EXPORT_SIGNING_PUBKEY", "public_key.pem")
    with open(pubkey_path, "rb") as key_file:
        public_key = load_pem_public_key(key_file.read(), backend=default_backend())
    with open(csv_file + ".hash", "r", encoding="utf-8") as hfile:
        last_hash = hfile.readlines()[-1].strip().encode()
    with open(csv_file + ".sig", "rb") as sigfile:
        signature = sigfile.read()
    try:
        public_key.verify(
            signature,
            last_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        print("Signature verified.")
        return True
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_export.py <csv_file> [public_key.pem]")
        sys.exit(1)
    csv_file = sys.argv[1]
    pubkey_path = sys.argv[2] if len(sys.argv) > 2 else None
    ok1 = verify_hash_chain(csv_file)
    ok2 = verify_signature(csv_file, pubkey_path)
    if ok1 and ok2:
        print("Export is authentic and untampered.")
    else:
        print("Export failed verification.")
