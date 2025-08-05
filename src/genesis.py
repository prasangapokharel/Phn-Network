import json
import os
import time
import hashlib
from wallet import get_display_address
from config import OWNER_ALLOCATION, BLOCKCHAIN_FILE

blockchain = []  # Will be imported in main to access global chain

def save_blockchain(blockchain_data):
    try:
        with open(BLOCKCHAIN_FILE, "w") as f:
            json.dump(blockchain_data, f, indent=4)
        print(f"Blockchain saved to {BLOCKCHAIN_FILE}")
    except Exception as e:
        print(f"Error saving blockchain: {e}")

def load_blockchain():
    global blockchain
    if os.path.exists(BLOCKCHAIN_FILE):
        try:
            with open(BLOCKCHAIN_FILE, "r") as f:
                loaded = json.load(f)
                if isinstance(loaded, list) and len(loaded) > 0:
                    blockchain = loaded
                    print(f"Blockchain loaded. Length: {len(blockchain)}")
                    return blockchain
                else:
                    print("Invalid blockchain data, starting fresh.")
                    blockchain = []
                    return []
        except Exception as e:
            print(f"Error loading blockchain: {e}, starting fresh.")
            blockchain = []
            return []
    else:
        print("No blockchain file found, starting fresh.")
        blockchain = []
        return []

def hash_block(block):
    block_copy = {k: v for k, v in block.items() if k != "hash"}
    block_str = json.dumps(block_copy, sort_keys=True).encode()
    return hashlib.sha256(block_str).hexdigest()

def create_genesis_block(owner_address):
    genesis_tx = {
        "sender": "coinbase",
        "recipient": owner_address,
        "amount": OWNER_ALLOCATION,
        "timestamp": time.time(),
        "txid": hashlib.sha256(f"genesis_tx_{owner_address}_{time.time()}".encode()).hexdigest(),
        "signature": "genesis_signature"
    }
    block = {
        "index": 0,
        "timestamp": time.time(),
        "transactions": [genesis_tx],
        "prev_hash": "0",
        "nonce": 0,
    }
    block["hash"] = hash_block(block)
    return block
