import asyncio
import websockets
import json
import time
import hashlib
import argparse # Import argparse for command-line arguments
from ecdsa import SigningKey, SECP256k1
from wallet import load_wallet, generate_wallet, save_wallet, get_display_address
from config import NODE_PORT, DIFFICULTY, BLOCK_REWARD

NODE_URL = f"ws://localhost:{NODE_PORT}"
MINING_INTERVAL = 1 # seconds to wait if no pending transactions

async def get_pending_transactions(ws):
    """Request pending transactions from the node"""
    await ws.send(json.dumps({"type": "get_pending"}))
    response = await ws.recv()
    data = json.loads(response)
    return data.get("pending_transactions", [])

async def get_blockchain_info(ws):
    """Request blockchain info from the node"""
    await ws.send(json.dumps({"type": "get_blockchain"}))
    response = await ws.recv()
    data = json.loads(response)
    return data.get("blockchain", []), data.get("length", 0)

async def submit_block(ws, block):
    """Submit a mined block to the node"""
    await ws.send(json.dumps({"type": "submit_block", "block": block}))
    response = await ws.recv()
    return json.loads(response)

def hash_block(block):
    """Create hash of a block (same as node)"""
    block_copy = {k: v for k, v in block.items() if k != 'hash'}
    block_str = json.dumps(block_copy, sort_keys=True).encode()
    return hashlib.sha256(block_str).hexdigest()

async def mine(miner_canonical_address, sk):
    """Mining loop"""
    print(f"⛏️ Miner started for address: {get_display_address(miner_canonical_address)} ({miner_canonical_address[:8]}...)")
    print(f"   All mining rewards will be sent to this address.")
    print(f"   Connecting to node: {NODE_URL}")

    try:
        async with websockets.connect(NODE_URL) as ws:
            print("✅ Connected to node!")
            
            while True:
                # 1. Get current blockchain info
                blockchain, chain_length = await get_blockchain_info(ws)
                if not blockchain:
                    print("Waiting for blockchain data from node...")
                    await asyncio.sleep(MINING_INTERVAL)
                    continue

                last_block = blockchain[-1]
                
                # 2. Get pending transactions
                pending = await get_pending_transactions(ws)
                
                if not pending:
                    print(f"No pending transactions. Waiting {MINING_INTERVAL}s...")
                    await asyncio.sleep(MINING_INTERVAL)
                    continue
                
                print(f"\nFound {len(pending)} pending transactions. Starting mining...")
                
                # 3. Create coinbase transaction for block reward
                coinbase_tx = {
                    "sender": "coinbase",
                    "recipient": miner_canonical_address, # Canonical address for mining reward
                    "amount": BLOCK_REWARD,
                    "timestamp": time.time(),
                    "txid": hashlib.sha256(f"coinbase_{miner_canonical_address}_{time.time()}".encode()).hexdigest(),
                    "signature": "coinbase_signature"
                }
                
                # 4. Build block candidate
                block_candidate = {
                    "index": chain_length,
                    "timestamp": time.time(),
                    "transactions": [coinbase_tx] + pending, # Coinbase first, then pending
                    "prev_hash": last_block["hash"],
                    "nonce": 0
                }
                
                # 5. Perform Proof of Work
                target_prefix = '0' * DIFFICULTY
                nonce = 0
                start_time = time.time()
                
                while True:
                    block_candidate["nonce"] = nonce
                    current_hash = hash_block(block_candidate)
                    
                    if current_hash.startswith(target_prefix):
                        block_candidate["hash"] = current_hash
                        end_time = time.time()
                        print(f"🎉 Block #{block_candidate['index']} mined in {end_time - start_time:.2f}s!")
                        print(f"   Hash: {current_hash}")
                        print(f"   Nonce: {nonce}")
                        break
                    
                    nonce += 1
                    if nonce % 100000 == 0:
                        print(f"   Mining... tried {nonce} nonces. Current hash: {current_hash[:10]}...")
                
                # 6. Submit block to node
                print("Submitting block to node...")
                submit_response = await submit_block(ws, block_candidate)
                
                if submit_response.get("status") == "success":
                    print("✅ Block accepted by node!")
                else:
                    print(f"❌ Block rejected by node: {submit_response.get('message', 'Unknown error')}")
                
                # Wait a bit before trying again to avoid spamming the node
                await asyncio.sleep(1) 
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection to node closed: {e}")
        print(f"   Retrying connection in {MINING_INTERVAL*2}s...")
        await asyncio.sleep(MINING_INTERVAL * 2)
    except ConnectionRefusedError:
        print(f"❌ Connection refused. Is the node running at {NODE_URL}?")
        print(f"   Retrying connection in {MINING_INTERVAL*2}s...")
        await asyncio.sleep(MINING_INTERVAL * 2)
    except Exception as e:
        print(f"❌ Miner error: {e}")
        import traceback
        traceback.print_exc()
        await asyncio.sleep(MINING_INTERVAL * 2)

async def main():
    """Main function for miner script, handles wallet selection/generation."""
    parser = argparse.ArgumentParser(description="PHN Blockchain Miner")
    parser.add_argument('--wallet', '-w', type=str, help='Path to an existing wallet file (e.g., wallet.txt, owner.txt).')
    parser.add_argument('--generate', '-g', action='store_true', help='Generate a new wallet for mining rewards and save it to mined.txt.')
    
    args = parser.parse_args()

    sk = None
    miner_canonical_address = None
    wallet_filename = "wallet.txt" # Default wallet file

    if args.generate:
        wallet_filename = "mined.txt"
        print(f"Generating a new wallet for mining rewards and saving to {wallet_filename}...")
        sk, miner_canonical_address = generate_wallet()
        save_wallet(sk, miner_canonical_address, wallet_filename)
        print(f"New miner wallet generated and saved to {wallet_filename}.")
    elif args.wallet:
        wallet_filename = args.wallet
        print(f"Loading miner wallet from {wallet_filename}...")
        sk, miner_canonical_address = load_wallet(wallet_filename)
        print(f"Miner wallet loaded from {wallet_filename}.")
    else:
        print(f"No wallet specified. Loading default miner wallet from {wallet_filename}...")
        sk, miner_canonical_address = load_wallet(wallet_filename)
        print(f"Default miner wallet loaded from {wallet_filename}.")

    await mine(miner_canonical_address, sk)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Miner stopped.")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
