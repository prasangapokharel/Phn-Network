from ecdsa import SigningKey, SECP256k1
import hashlib

def get_display_address(canonical_public_key_hex: str) -> str:
    public_key_bytes = bytes.fromhex(canonical_public_key_hex)
    address_hash = hashlib.sha256(public_key_bytes).hexdigest()[:40]
    return f"PHN{address_hash}"

def generate_wallet():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()

    private_key_hex = sk.to_string().hex()              
    canonical_address = vk.to_string().hex()             
    display_address = get_display_address(canonical_address)

    return private_key_hex, canonical_address, display_address

if __name__ == "__main__":
    print("=== Generate New PHN Wallet ===")
    priv_key, canonical_addr, phn_addr = generate_wallet()
    print(f"Private Key (hex): {priv_key}")
    print(f"Canonical Address (128-char hex): {canonical_addr}")
    print(f"PHN Display Address: {phn_addr}")

