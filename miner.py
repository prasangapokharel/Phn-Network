import asyncio
import websockets
import json
import time
import hashlib
import argparse
from ecdsa import SigningKey, SECP256k1

# Node WebSocket URL (hardcoded or could come from .env or argument)
NODE_URL = "ws://31.97.229.45:8765"  # replace port if needed
MINING_INTERVAL = 1  # seconds

# --- Wallet utilities ---
def generate_wallet():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    canonical_pub = vk.to_string().hex()
    return sk, canonical_pub

def get_display_address(canonical_pub_hex):
    pub_bytes = bytes.fromhex(canonical_pub_hex)
    return "PHN" + hashlib.sha256(pub_bytes).hexdigest()[:40]

# --- Blockchain communication ---
async def get_node_info(ws):
    """Fetch node info like difficulty and block reward from the node."""
    await ws.send(json.dumps({"type": "get_node_info"}))
    data = json.loads(await ws.recv())
    # Expected response keys: difficulty, block_reward
    difficulty = data.get("difficulty", 4)  # default fallback
    block_reward = data.get("block_reward", 1)  # default fallback
    return difficulty, block_reward

async def get_pending_transactions(ws):
    await ws.send(json.dumps({"type": "get_pending"}))
    data = json.loads(await ws.recv())
    return data.get("pending_transactions", [])

async def get_blockchain_info(ws):
    await ws.send(json.dumps({"type": "get_blockchain"}))
    data = json.loads(await ws.recv())
    return data.get("blockchain", []), data.get("length", 0)

async def submit_block(ws, block):
    await ws.send(json.dumps({"type": "submit_block", "block": block}))
    return json.loads(await ws.recv())

# --- Mining utilities ---
def hash_block(block):
    block_copy = {k: v for k, v in block.items() if k != 'hash'}
    return hashlib.sha256(json.dumps(block_copy, sort_keys=True).encode()).hexdigest()

async def mine(miner_canonical_address):
    print(f"⛏️ Miner started for address: {get_display_address(miner_canonical_address)}")
    print(f"   Connecting to node: {NODE_URL}")

    try:
        async with websockets.connect(NODE_URL) as ws:
            print("✅ Connected to node!")

            difficulty, block_reward = await get_node_info(ws)
            print(f"⚙️ Difficulty: {difficulty}, Block Reward: {block_reward}")

            while True:
                blockchain, chain_length = await get_blockchain_info(ws)
                if not blockchain:
                    print("Waiting for blockchain data...")
                    await asyncio.sleep(MINING_INTERVAL)
                    continue

                last_block = blockchain[-1]
                pending = await get_pending_transactions(ws)

                if not pending:
                    print(f"No pending tx. Waiting {MINING_INTERVAL}s...")
                    await asyncio.sleep(MINING_INTERVAL)
                    continue

                print(f"\nFound {len(pending)} pending transactions. Mining...")

                # Coinbase transaction paying miner the block reward
                coinbase_tx = {
                    "sender": "coinbase",
                    "recipient": miner_canonical_address,
                    "amount": block_reward,
                    "timestamp": time.time(),
                    "txid": hashlib.sha256(f"coinbase_{miner_canonical_address}_{time.time()}".encode()).hexdigest(),
                    "signature": "coinbase_signature"
                }

                # Prepare block candidate
                block_candidate = {
                    "index": chain_length,
                    "timestamp": time.time(),
                    "transactions": [coinbase_tx] + pending,
                    "prev_hash": last_block["hash"],
                    "nonce": 0
                }

                target_prefix = '0' * difficulty
                nonce = 0
                start_time = time.time()

                while True:
                    block_candidate["nonce"] = nonce
                    current_hash = hash_block(block_candidate)

                    if current_hash.startswith(target_prefix):
                        block_candidate["hash"] = current_hash
                        print(f"🎉 Block #{block_candidate['index']} mined in {time.time() - start_time:.2f}s!")
                        print(f"   Hash: {current_hash}")
                        break

                    nonce += 1
                    if nonce % 100000 == 0:
                        print(f"   Tried {nonce} nonces... Current hash: {current_hash[:12]}")

                print("Submitting block...")
                resp = await submit_block(ws, block_candidate)

                if resp.get("status") == "success":
                    print("✅ Block accepted by node!")
                else:
                    print(f"❌ Block rejected: {resp.get('message', 'Unknown error')}")

                await asyncio.sleep(1)

    except Exception as e:
        print(f"❌ Miner error: {e}")
        await asyncio.sleep(MINING_INTERVAL * 2)

# --- Main entry ---
async def main():
    parser = argparse.ArgumentParser(description="PHN Miner")
    parser.add_argument('-g', '--generate', action='store_true', help="Generate new wallet for mining")
    parser.add_argument('-p', '--private', type=str, help="Use existing private key (hex)")
    args = parser.parse_args()

    if args.generate:
        sk, miner_canonical_address = generate_wallet()
        print(f"Generated Wallet:\n Private Key: {sk.to_string().hex()}\n Address: {get_display_address(miner_canonical_address)}")
    elif args.private:
        try:
            sk = SigningKey.from_string(bytes.fromhex(args.private), curve=SECP256k1)
            miner_canonical_address = sk.get_verifying_key().to_string().hex()
            print(f"Using provided key. Address: {get_display_address(miner_canonical_address)}")
        except:
            print("❌ Invalid private key")
            return
    else:
        sk, miner_canonical_address = generate_wallet()
        print(f"Generated Wallet:\n Private Key: {sk.to_string().hex()}\n Address: {get_display_address(miner_canonical_address)}")

    await mine(miner_canonical_address)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Miner stopped.")
