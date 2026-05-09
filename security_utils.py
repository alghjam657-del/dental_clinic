import hashlib
import hmac
import re
from typing import Tuple

from werkzeug.security import check_password_hash, generate_password_hash

_SHA256_HEX_RE = re.compile(r"^[a-fA-F0-9]{64}$")


def hash_password(password: str) -> str:
    """Create a modern password hash for new/updated passwords."""
    return generate_password_hash(password)


def verify_password(stored_password: str, candidate_password: str) -> Tuple[bool, bool]:
    """
    Verify password across multiple legacy formats.

    Returns:
      (is_valid, needs_rehash)
    """
    if not stored_password:
        return False, False

    # Modern Werkzeug hashes (pbkdf2/scrypt).
    if stored_password.startswith(("pbkdf2:", "scrypt:")):
        try:
            valid = check_password_hash(stored_password, candidate_password)
            return valid, False
        except ValueError:
            return False, False

    # Legacy SHA-256 hex.
    if _SHA256_HEX_RE.match(stored_password):
        digest = hashlib.sha256(candidate_password.encode("utf-8")).hexdigest()
        valid = hmac.compare_digest(stored_password.lower(), digest.lower())
        return valid, valid

    # Legacy plain text (fallback for old data imports).
    valid = hmac.compare_digest(stored_password, candidate_password)
    return valid, valid
