import base64
import hashlib
import secrets


def hash_password(password):
    if not 12 <= len(password) <= 256:
        raise ValueError('Password must contain 12–256 characters')
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=32768, r=8, p=3, maxmem=64*1024*1024)
    return 'scrypt$'+base64.b64encode(salt).decode()+'$'+base64.b64encode(key).decode()


def verify_password(password, encoded):
    try:
        scheme, salt, expected = encoded.split('$')
        if scheme != 'scrypt' or len(password) > 256:
            return False
        key = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=32768, r=8, p=3, maxmem=64*1024*1024)
        return secrets.compare_digest(key, base64.b64decode(expected))
    except (ValueError, TypeError):
        return False
