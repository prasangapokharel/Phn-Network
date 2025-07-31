from ecdsa import SigningKey, VerifyingKey, SECP256k1
import os
import hashlib

def get_display_address(public_key_hex):
    """Derive a human-readable 'PHN' address from the raw public key hex."""
    try:
        public_key_bytes = bytes.fromhex(public_key_hex)
        address_hash = hashlib.sha256(public_key_bytes).hexdigest()[:40] # Use first 40 chars of SHA256 hash
        return f"PHN{address_hash}"
    except Exception as e:
        print(f"Error deriving display address for {public_key_hex}: {e}")
        return "INVALID_ADDRESS"

def generate_wallet():
    """Generate a new wallet with private key and raw public key hex (canonical address)."""
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    
    # The canonical address is the hex representation of the raw public key
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
    """Load wallet from a specified file. Raises error if file not found or invalid."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Wallet file {filename} not found.")
    
    try:
        with open(filename, "r") as f:
            lines = f.read().strip().splitlines()
            if len(lines) < 2:
                raise ValueError("Invalid wallet file format: expected private key and canonical address.")
            
            sk_hex = lines[0].strip()
            canonical_address = lines[1].strip()
        
        if len(sk_hex) != 64: # 32 bytes = 64 hex chars
            raise ValueError("Invalid private key hex length.")
        
        sk = SigningKey.from_string(bytes.fromhex(sk_hex), curve=SECP256k1)
        
        # Verify if the loaded canonical address matches the public key derived from the private key
        derived_canonical_address = sk.get_verifying_key().to_string().hex()
        if derived_canonical_address != canonical_address:
            raise ValueError("Canonical address in file does not match derived public key.")
            
        return sk, canonical_address
        
    except Exception as e:
        raise Exception(f"Error loading wallet from {filename}: {e}")

if __name__ == "__main__":
    # When wallet.py is run directly, it only generates and prints a new wallet.
    # It does NOT automatically save it to wallet.txt.
    print("Generating a new wallet (private key and address)...")
    new_sk, new_canonical_address = generate_wallet()
    new_display_address = get_display_address(new_canonical_address)

    print("\n--- NEW WALLET GENERATED ---")
    print(f"Private Key (hex): {new_sk.to_string().hex()}")
    print(f"Canonical Address (for blockchain): {new_canonical_address}")
    print(f"Display Address (PHN format): {new_display_address}")
    print("----------------------------")
    print("\nTo save this wallet, copy the private key and canonical address into a 'wallet.txt' file.")
    print("Example wallet.txt content:")
    print(f"{new_sk.to_string().hex()}")
    print(f"{new_canonical_address}")
