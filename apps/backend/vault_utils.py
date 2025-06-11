import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError


def get_private_key_from_aws(secret_id=None, region=None):
    secret_id = secret_id or os.getenv("AWS_SECRET_ID", "fin-observability-signing-key")
    region = region or os.getenv("AWS_REGION", "us-east-1")
    try:
        client = boto3.client("secretsmanager", region_name=region)
        get_secret_value_response = client.get_secret_value(SecretId=secret_id)
        secret = get_secret_value_response["SecretString"]
        # Assume the secret is the PEM-encoded private key
        return secret.encode()
    except NoCredentialsError:
        raise RuntimeError("AWS credentials not available for Secrets Manager.")
    except ClientError as e:
        raise RuntimeError(f"Could not retrieve secret: {e}")
    except Exception as e:
        raise RuntimeError(f"Unknown error fetching secret: {e}")


# Add more vault providers as needed (e.g., HashiCorp Vault)


def get_private_key_from_vault():
    vault_type = os.getenv("VAULT_TYPE", "aws").lower()
    if vault_type == "aws":
        return get_private_key_from_aws()
    # Future: elif vault_type == "hashicorp": ...
    else:
        raise RuntimeError(f"Vault type '{vault_type}' not supported.")
