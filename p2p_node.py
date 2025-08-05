import asyncio
import websockets
import json
import time
import hashlib
import os # Import os for file path operations
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
from wallet import load_wallet, get_display_address
from config import NODE_PORT, DIFFICULTY, BLOCK_REWARD, TOTAL_SUPPLY, MINABLE_SUPPLY, OWNER_ALLOCATION
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()


# Get variables
node_url = os.getenv("NODE_URL")
node_port = os.getenv("NODE_PORT")

# Global variables
blockchain = []
pending_txs = []
sk, OWNER_ADDRESS = None, None # OWNER_ADDRESS will now be the canonical (raw public key hex) of the owner

# File for blockchain persistence
BLOCKCHAIN_FILE = "blockchain.json"

def save_blockchain():
    """Saves the current blockchain to a JSON file."""
    try:
        with open(BLOCKCHAIN_FILE, "w") as f:
            json.dump(blockchain, f, indent=4)
        print(f"Blockchain saved to {BLOCKCHAIN_FILE}")
    except Exception as e:
        print(f" Error saving blockchain: {e}")

def load_blockchain():
    """Loads the blockchain from a JSON file."""
    global blockchain
    if os.path.exists(BLOCKCHAIN_FILE):
        try:
            with open(BLOCKCHAIN_FILE, "r") as f:
                loaded_blockchain = json.load(f)
                # Basic validation: check if it's a list and has at least a genesis block
                if isinstance(loaded_blockchain, list) and len(loaded_blockchain) > 0:
                    blockchain = loaded_blockchain
                    print(f"Blockchain loaded from {BLOCKCHAIN_FILE}. Length: {len(blockchain)}")
                    return True
                else:
                    print(f"Invalid blockchain data in {BLOCKCHAIN_FILE}. Starting fresh.")
                    blockchain = [] # Reset if invalid
                    return False
        except json.JSONDecodeError as e:
            print(f" Error decoding blockchain from {BLOCKCHAIN_FILE}: {e}. Starting fresh.")
            blockchain = [] # Reset if corrupted
            return False
        except Exception as e:
            print(f" Error loading blockchain from {BLOCKCHAIN_FILE}: {e}. Starting fresh.")
            blockchain = [] # Reset on other errors
            return False
    else:
        print(f"No existing blockchain file found at {BLOCKCHAIN_FILE}. A new genesis block will be created.")
        return False

def initialize_node():
    """Initialize the node with owner wallet and blockchain (from file or new genesis)"""
    global sk, OWNER_ADDRESS, blockchain
    
    # Load the owner's wallet from owner.txt
    try:
        sk, OWNER_ADDRESS = load_wallet("owner.txt") # OWNER_ADDRESS is the canonical address
        print(f"Node initialized with owner wallet: {get_display_address(OWNER_ADDRESS)} ({OWNER_ADDRESS[:8]}...)")
    except Exception as e:
        print(f" Error loading owner wallet from owner.txt: {e}")
        print("Please run 'python owner.py' first to set up the owner wallet.")
        exit(1) # Exit if owner wallet cannot be loaded/created

    # Attempt to load existing blockchain
    blockchain_loaded = load_blockchain()

    # Create genesis block if blockchain is empty (either no file or invalid/empty file)
    if not blockchain_loaded or not blockchain:
        genesis_block = create_genesis_block()
        blockchain.append(genesis_block)
        print("Genesis block created")
        save_blockchain() # Save genesis block immediately

def hash_block(block):
    """Create hash of a block"""
    try:
        # Create a copy without the hash field for hashing
        block_copy = {k: v for k, v in block.items() if k != 'hash'}
        block_str = json.dumps(block_copy, sort_keys=True).encode()
        return hashlib.sha256(block_str).hexdigest()
    except Exception as e:
        print(f"Error hashing block: {e}")
        return "error_hash"

def create_genesis_block():
    """Create the first block in the blockchain with owner allocation."""
    # Coinbase transaction for owner's initial allocation
    genesis_tx = {
        "sender": "coinbase", # Special sender for newly minted coins
        "recipient": OWNER_ADDRESS, # Canonical address of the owner's wallet
        "amount": OWNER_ALLOCATION, # Initial allocation for the owner
        "timestamp": time.time(),
        "txid": hashlib.sha256(f"genesis_tx_{OWNER_ADDRESS}_{time.time()}".encode()).hexdigest(),
        "signature": "genesis_signature" # No actual signature for coinbase
    }

    block = {
        "index": 0,
        "timestamp": time.time(),
        "transactions": [genesis_tx],
        "prev_hash": "0",
        "nonce": 0
    }
    block["hash"] = hash_block(block)
    return block

def get_balance(address):
    """Calculate balance for an address by summing transactions in the blockchain.
    Address here is the canonical (raw public key hex) address."""
    balance = 0
    for block in blockchain:
        for tx in block["transactions"]:
            if tx["sender"] == address:
                balance -= tx["amount"]
            elif tx["recipient"] == address:
                balance += tx["amount"]
    return balance

def verify_signature(tx):
    """Verify transaction signature cryptographically.
    tx['sender'] must be the canonical (raw public key hex) address."""
    if tx["sender"] == "coinbase": # Coinbase transactions don't have a real signature
        return True

    try:
        signature = bytes.fromhex(tx["signature"])
        # The sender is the canonical (raw public key hex) address
        sender_vk = VerifyingKey.from_string(bytes.fromhex(tx["sender"]), curve=SECP256k1)
        message = f"{tx['sender']}{tx['recipient']}{tx['amount']}{tx['timestamp']}".encode()
        return sender_vk.verify(signature, message)
    except (BadSignatureError, Exception) as e:
        print(f"Signature verification failed for TX {tx.get('txid', 'N/A')}: {e}")
        return False

def validate_transaction(tx):
    """Validate a transaction.
    tx['sender'] and tx['recipient'] must be canonical addresses."""
    # Check required fields
    required_fields = ["sender", "recipient", "amount", "timestamp", "signature"]
    for field in required_fields:
        if field not in tx:
            return False, f"Missing field: {field}"
    
    # Check amount is positive
    if tx["amount"] <= 0:
        return False, "Amount must be positive"
    
    # Check sender has sufficient balance (only for non-coinbase transactions)
    if tx["sender"] != "coinbase":
        sender_balance = get_balance(tx["sender"])
        if sender_balance < tx["amount"]:
            return False, f"Insufficient balance. Have: {sender_balance}, Need: {tx['amount']}"
    
    # Verify signature
    if not verify_signature(tx):
        return False, "Invalid signature"
    
    return True, "Valid transaction"

def validate_block(block):
    """Validate a submitted block."""
    print(f"Validating block #{block.get('index')}")
    # 1. Check block structure
    required_fields = ["index", "timestamp", "transactions", "prev_hash", "nonce", "hash"]
    for field in required_fields:
        if field not in block:
            return False, f"Block missing field: {field}"

    # 2. Verify block hash
    if hash_block(block) != block["hash"]:
        return False, "Invalid block hash"

    # 3. Verify Proof of Work
    if not block["hash"].startswith('0' * DIFFICULTY):
        return False, f"Invalid Proof of Work (hash does not meet difficulty {DIFFICULTY})"

    # 4. Check index and previous hash
    # This check needs to be careful if the node just started and loaded a chain
    # or if it's receiving a block from a peer that's ahead.
    # For now, we assume a single node and sequential block addition.
    if block["index"] != len(blockchain):
        return False, f"Invalid block index. Expected {len(blockchain)}, got {block['index']}"
    if block["index"] > 0 and block["prev_hash"] != blockchain[-1]["hash"]:
        return False, "Invalid previous hash"

    # 5. Validate transactions within the block
    coinbase_tx_count = 0
    block_reward_sum = 0
    seen_tx_ids = set()
    
    for tx in block["transactions"]:
        if "txid" not in tx:
            return False, "Transaction missing txid"
        if tx["txid"] in seen_tx_ids:
            return False, f"Duplicate transaction ID in block: {tx['txid']}"
        seen_tx_ids.add(tx["txid"])

        if tx["sender"] == "coinbase":
            coinbase_tx_count += 1
            block_reward_sum += tx["amount"]
            
            if block["index"] == 0: # Genesis block
                if tx["amount"] != OWNER_ALLOCATION:
                    return False, f"Invalid genesis block reward amount. Expected {OWNER_ALLOCATION}, got {tx['amount']}"
                if tx["recipient"] != OWNER_ADDRESS:
                    return False, f"Invalid genesis block recipient. Expected {OWNER_ADDRESS}, got {tx['recipient']}"
            else: # Subsequent blocks
                if tx["amount"] != BLOCK_REWARD:
                    return False, f"Invalid block reward amount. Expected {BLOCK_REWARD}, got {tx['amount']}"
            
            if coinbase_tx_count > 1:
                return False, "Multiple coinbase transactions in block"
        else:
            is_valid, error_msg = validate_transaction(tx)
            if not is_valid:
                return False, f"Invalid transaction in block: {error_msg}"
    
    if coinbase_tx_count != 1:
        return False, "Block must contain exactly one coinbase transaction"
    
    # For genesis block, block_reward_sum should be OWNER_ALLOCATION
    # For subsequent blocks, block_reward_sum should be BLOCK_REWARD
    expected_reward = OWNER_ALLOCATION if block["index"] == 0 else BLOCK_REWARD
    if block_reward_sum != expected_reward:
        return False, f"Total block reward mismatch. Expected {expected_reward}, got {block_reward_sum}"

    return True, "Block is valid"

async def handle_send_transaction(ws, msg):
    """Handle transaction submission.
    tx['sender'] and tx['recipient'] are expected to be canonical addresses."""
    try:
        tx = msg.get("tx")
        if not tx:
            await ws.send(json.dumps({"error": "No transaction provided"}))
            return
        
        # Validate transaction
        is_valid, error_msg = validate_transaction(tx)
        if not is_valid:
            await ws.send(json.dumps({"error": error_msg}))
            return
        
        # Add transaction ID if not present
        if "txid" not in tx:
            message = f"{tx['sender']}{tx['recipient']}{tx['amount']}{tx['timestamp']}".encode()
            tx["txid"] = hashlib.sha256(message).hexdigest()
        
        # Check for duplicate in pending_txs
        if any(p_tx["txid"] == tx["txid"] for p_tx in pending_txs):
            await ws.send(json.dumps({"error": "Transaction already in mempool"}))
            return

        # Add to pending transactions
        pending_txs.append(tx)
        print(f"✅ Transaction added: {get_display_address(tx['sender'])} -> {get_display_address(tx['recipient'])} ({tx['amount']} PHN)")
        
        await ws.send(json.dumps({
            "status": "success",
            "message": "Transaction received and added to mempool",
            "txid": tx["txid"]
        }))
    except Exception as e:
        print(f"Error handling send transaction: {e}")
        await ws.send(json.dumps({"error": f"Internal error: {str(e)}"}))

async def handle_get_balance(ws, msg):
    """Handle balance query.
    Expected 'address' in msg is the canonical address."""
    try:
        address = msg.get("address")
        if not address:
            await ws.send(json.dumps({"error": "No address provided"}))
            return
        
        balance = get_balance(address)
        print(f"💰 Balance query for {get_display_address(address)}: {balance} PHN")
        
        await ws.send(json.dumps({
            "address": address, # Return canonical address
            "display_address": get_display_address(address), # Also return display address
            "balance": balance
        }))
    except Exception as e:
        print(f"Error handling get balance: {e}")
        await ws.send(json.dumps({"error": f"Internal error: {str(e)}"}))

async def handle_get_blockchain(ws, msg):
    """Handle blockchain query.
    Converts sender/recipient addresses in transactions to display format for output."""
    try:
        # Create a copy of the blockchain with display addresses for transactions
        display_blockchain = []
        for block in blockchain:
            display_block = block.copy()
            display_block_txs = []
            for tx in block["transactions"]:
                display_tx = tx.copy()
                if display_tx["sender"] != "coinbase":
                    display_tx["sender_display"] = get_display_address(display_tx["sender"])
                display_tx["recipient_display"] = get_display_address(display_tx["recipient"])
                display_block_txs.append(display_tx)
            display_block["transactions"] = display_block_txs
            display_blockchain.append(display_block)

        await ws.send(json.dumps({
            "blockchain": display_blockchain,
            "length": len(blockchain)
        }))
    except Exception as e:
        print(f"Error handling get blockchain: {e}")
        await ws.send(json.dumps({"error": f"Internal error: {str(e)}"}))

async def handle_get_pending(ws, msg):
    """Handle pending transactions query.
    Converts sender/recipient addresses to display format for output."""
    try:
        display_pending_txs = []
        for tx in pending_txs:
            display_tx = tx.copy()
            display_tx["sender_display"] = get_display_address(display_tx["sender"])
            display_tx["recipient_display"] = get_display_address(display_tx["recipient"])
            display_pending_txs.append(display_tx)

        await ws.send(json.dumps({
            "pending_transactions": display_pending_txs,
            "count": len(pending_txs)
        }))
    except Exception as e:
        print(f"Error handling get pending: {e}")
        await ws.send(json.dumps({"error": f"Internal error: {str(e)}"}))

async def handle_submit_block(ws, msg):
    """Handle submitted block from a miner."""
    block = msg.get("block")
    if not block:
        await ws.send(json.dumps({"error": "No block provided"}))
        return
    
    is_valid, error_msg = validate_block(block)
    if not is_valid:
        print(f" Invalid block submitted: {error_msg}")
        await ws.send(json.dumps({"status": "error", "message": error_msg}))
        return
    
    # Add block to blockchain
    blockchain.append(block)
    save_blockchain() # Save blockchain after adding a new block
    
    # Remove included transactions from pending_txs
    mined_tx_ids = {tx["txid"] for tx in block["transactions"] if tx["sender"] != "coinbase"}
    global pending_txs
    pending_txs = [tx for tx in pending_txs if tx["txid"] not in mined_tx_ids]
    
    print(f" Block #{block['index']} accepted! Mined by {get_display_address(block['transactions'][0]['recipient'])}")
    print(f"   New blockchain length: {len(blockchain)}")
    print(f"   Pending transactions remaining: {len(pending_txs)}")
    
    await ws.send(json.dumps({"status": "success", "message": "Block accepted!"}))

async def handle_message(ws, message):
    """Handle incoming WebSocket messages"""
    try:
        msg = json.loads(message)
        print(f" Received message: {msg.get('type', 'unknown')}")
    except json.JSONDecodeError as e:
        print(f" Invalid JSON: {e}")
        try:
            await ws.send(json.dumps({"error": "Invalid JSON"}))
        except:
            pass
        return
    except Exception as e:
        print(f" Error parsing message: {e}")
        return
    
    message_type = msg.get("type")
    
    try:
        if message_type == "send_tx":
            await handle_send_transaction(ws, msg)
        elif message_type == "get_balance":
            await handle_get_balance(ws, msg)
        elif message_type == "get_blockchain":
            await handle_get_blockchain(ws, msg)
        elif message_type == "get_pending":
            await handle_get_pending(ws, msg)
        elif message_type == "submit_block":
            await handle_submit_block(ws, msg)
        else:
            await ws.send(json.dumps({"error": "Unknown message type"}))
    except Exception as e:
        print(f" Error handling message type '{message_type}': {e}")
        try:
            await ws.send(json.dumps({"error": f"Internal server error: {str(e)}"}))
        except:
            pass

async def handler(websocket):
    """WebSocket connection handler"""
    client_address = None
    try:
        client_address = websocket.remote_address
        print(f"🔗 Client connected: {client_address}")
        
        async for message in websocket:
            await handle_message(websocket, message)
            
    except websockets.exceptions.ConnectionClosed:
        print(f"🔌 Client disconnected: {client_address}")
    except Exception as e:
        print(f"Handler error for {client_address}: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main server function"""
    try:
        # Initialize node
        initialize_node()
        
        print(f" P2P Blockchain Node starting...")
        print(f"WebSocket server: {node_url}{node_port}")        
        print(f"   Owner address (canonical): {OWNER_ADDRESS[:8]}...")
        print(f"   Owner address (display): {get_display_address(OWNER_ADDRESS)}")
        print(f"   Owner balance: {get_balance(OWNER_ADDRESS)} PHN (initial allocation from genesis)")
        print(f"   Blockchain length: {len(blockchain)}")
        print(f"   Minable supply remaining: {MINABLE_SUPPLY - (len(blockchain) - 1) * BLOCK_REWARD} PHN")
        
        # Start WebSocket server
        server = await websockets.serve(handler, "localhost", NODE_PORT)
        
        print("✅ Node is running! Miners can now connect.")
        print("   Press Ctrl+C to stop.")
        
        await server.wait_closed()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down node...")
        save_blockchain() # Save blockchain on graceful shutdown
        if 'server' in locals():
            server.close()
            await server.wait_closed()
    except Exception as e:
        print(f" Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Node stopped.")
    except Exception as e:
        print(f" Fatal error: {e}")
