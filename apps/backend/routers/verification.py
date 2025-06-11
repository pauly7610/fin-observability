from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
from apps.backend import crypto_utils
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import hashlib

router = APIRouter(prefix="/verification", tags=["verification", "compliance"])


@router.post("/verify_export")
async def verify_export(
    csv_file: UploadFile = File(...),
    hash_file: UploadFile = File(...),
    sig_file: UploadFile = File(...),
    pubkey_file: UploadFile = File(None),
):
    """
    Verify hash chain and digital signature of an exported CSV file.
    """
    try:
        # Save uploaded files to temp
        temp_dir = "_tmp_verify"
        os.makedirs(temp_dir, exist_ok=True)
        csv_path = os.path.join(temp_dir, csv_file.filename)
        hash_path = os.path.join(temp_dir, hash_file.filename)
        sig_path = os.path.join(temp_dir, sig_file.filename)
        pubkey_path = None

        with open(csv_path, "wb") as f:
            f.write(await csv_file.read())
        with open(hash_path, "wb") as f:
            f.write(await hash_file.read())
        with open(sig_path, "wb") as f:
            f.write(await sig_file.read())
        if pubkey_file is not None:
            pubkey_path = os.path.join(temp_dir, pubkey_file.filename)
            with open(pubkey_path, "wb") as f:
                f.write(await pubkey_file.read())
        else:
            pubkey_path = os.getenv("EXPORT_SIGNING_PUBKEY", "public_key.pem")

        # --- Hash chain verification ---
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(hash_path, "r", encoding="utf-8") as f:
            hashes = [line.strip() for line in f.readlines()]
        prev_hash = ""
        computed_hashes = []
        for line in lines:
            data = (prev_hash + line).encode()
            h = hashlib.sha256(data).hexdigest()
            computed_hashes.append(h)
            prev_hash = h
        hash_chain_valid = computed_hashes == hashes
        last_hash = computed_hashes[-1] if computed_hashes else None

        # --- Signature verification ---
        with open(pubkey_path, "rb") as f:
            pubkey_data = f.read()
        public_key = serialization.load_pem_public_key(pubkey_data)
        with open(sig_path, "rb") as f:
            signature = f.read()
        try:
            public_key.verify(
                signature,
                last_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            signature_valid = True
        except Exception as e:
            signature_valid = False
        # Clean up temp files
        try:
            os.remove(csv_path)
            os.remove(hash_path)
            os.remove(sig_path)
            if pubkey_file is not None:
                os.remove(pubkey_path)
        except Exception:
            pass
        return JSONResponse(
            {
                "hash_chain_valid": hash_chain_valid,
                "signature_valid": signature_valid,
                "last_hash": last_hash,
                "detail": "Verification complete.",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
