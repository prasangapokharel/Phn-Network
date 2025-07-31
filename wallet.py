from ecdsa import SigningKey, VerifyingKey, SECP256k1
import os
import hashlib

def get_display_address(canonical_public_key_hex):
    """Derive a human-readable 'PHN' address from the raw public key hex."""
    try:
        public_key_bytes = bytes.fromhex(canonical_public_key_hex)
        address_hash = hashlib.sha256(public_key_bytes).hexdigest()[:40] # Use first 40 chars of SHA256 hash
        return f"PHN{address_hash}"
    except Exception as e:
        # Fallback for invalid input, though canonical_public_key_hex should always be valid here
        print(f"Error deriving display address for {canonical_public_key_hex}: {e}")
        return "INVALID_ADDRESS"

def generate_wallet():
    """Generate a new wallet with private key and raw public key hex (canonical address)."""
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    # The canonical address is the hex representation of the raw public key (128 chars)
    canonical_address = vk.to_string().hex()
    return sk, canonical_address

def save_wallet(sk, canonical_address, filename="wallet.txt"):
    """Save wallet (private key and canonical address) to a specified file."""
    try:
        with open(filename, "w") as f:
            f.write(f"{sk.to_string().hex()}\n")
            f.write(f"{canonical_address}\n")
        print(f"Wallet saved to {filename}")
    except Exception as e:
        print(f"Error saving wallet to {filename}: {e}")

def load_wallet(filename="wallet.txt"):
    """Load wallet from a specified file. If not found or invalid, generates a new one."""
    sk = None
    canonical_address = None

    if not os.path.exists(filename):
        print(f"Wallet file {filename} not found! Creating new wallet...")
        sk, canonical_address = generate_wallet()
        save_wallet(sk, canonical_address, filename)
        return sk, canonical_address
        
    try:
        with open(filename, "r") as f:
            lines = f.read().strip().splitlines()
            if len(lines) < 2:
                raise ValueError("Invalid wallet file format: expected private key and canonical address.")
            
            sk_hex = lines[0].strip()
            canonical_address = lines[1].strip()
        
        # Validate private key format
        if len(sk_hex) != 64: # 32 bytes = 64 hex chars
            raise ValueError("Invalid private key hex length.")
        
        sk = SigningKey.from_string(bytes.fromhex(sk_hex), curve=SECP256k1)
        
        # Verify if the loaded canonical address matches the public key derived from the private key
        derived_canonical_address = sk.get_verifying_key().to_string().hex()
        if derived_canonical_address != canonical_address:
            raise ValueError("Canonical address in file does not match derived public key.")
            
        return sk, canonical_address
            
    except Exception as e:
        print(f"Error loading wallet from {filename}: {e}")
        print("Creating new wallet...")
        sk, canonical_address = generate_wallet()
        save_wallet(sk, canonical_address, filename)
        return sk, canonical_address

if __name__ == "__main__":
    print("Testing wallet functionality...")
    # Load or generate a wallet
    sk, canonical_address = load_wallet()
    display_address = get_display_address(canonical_address)

    print("\n--- WALLET DETAILS ---")
    print(f"Private Key (hex): {sk.to_string().hex()}")
    print(f"Canonical Address (for blockchain): {canonical_address}")
    print(f"Display Address (PHN format): {display_address}")
    print("----------------------")
    print("\nNote: The 'canonical address' (128-char hex) is used internally for cryptographic operations.")
    print("The 'display address' (PHN format) is for user-friendly viewing and sharing.")
