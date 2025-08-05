import asyncio
import websockets
import json
import time
import hashlib
import argparse
from ecdsa import SigningKey, SECP256k1

NODE_URL = "ws://31.97.229.45:8765"
DIFFICULTY = 4       # Adjust as needed
MINING_INTERVAL = 1  # seconds

def get_display_address(canonical_pub_hex: str) -> str:
    pub_bytes = bytes.fromhex(canonical_pub_hex)
    address_hash = hashlib.sha256(pub_bytes).hexdigest()[:40]
    return f"PHN{address_hash}"

def generate_wallet():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    canonical_pub = vk.to_string().hex()
    return sk, canonical_pub

async def get_pending_transactions(ws):
    await ws.send(json.dumps({"type": "get_pending"}))
    response = await ws.recv()
    data = json.loads(response)
    return data.get("pending_transactions", [])

async def get_blockchain_info(ws):
    await ws.send(json.dumps({"type": "get_blockchain"}))
    response = await ws.recv()
    data = json.loads(response)
    return data.get("blockchain", []), data.get("length", 0)

async def submit_block(ws, block):
    await ws.send(json.dumps({"type": "submit_block", "block": block}))
    response = await ws.recv()
    return json.loads(response)

def hash_block(block):
    block_copy = {k: v for k, v in block.items() if k != 'hash'}
    block_str = json.dumps(block_copy, sort_keys=True).encode()
    return hashlib.sha256(block_str).hexdigest()

async def mine(miner_canonical_address, sk):
    display_address = get_display_address(miner_canonical_address)
    print(f"⛏️ Miner started for address: {display_address} ({miner_canonical_address[:8]}...)")
    print(f"   Connecting to node: {NODE_URL}")

    while True:
        try:
            async with websockets.connect(NODE_URL) as ws:
                print("✅ Connected to node!")

                while True:
                    blockchain, chain_length = await get_blockchain_info(ws)
                    if not blockchain:
                        print("Waiting for blockchain data from node...")
                        await asyncio.sleep(MINING_INTERVAL)
                        continue

                    last_block = blockchain[-1]
                    pending = await get_pending_transactions(ws)

                    if not pending:
                        print(f"No pending transactions. Waiting {MINING_INTERVAL}s...")
                        await asyncio.sleep(MINING_INTERVAL)
                        continue

                    print(f"\nFound {len(pending)} pending transactions. Starting mining...")

                    # Build block WITHOUT coinbase transaction (no mining reward)
                    block_candidate = {
                        "index": chain_length,
                        "timestamp": time.time(),
                        "transactions": pending,
                        "prev_hash": last_block["hash"],
                        "nonce": 0
                    }

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

                    print("Submitting block to node...")
                    submit_response = await submit_block(ws, block_candidate)

                    if submit_response.get("status") == "success":
                        print("✅ Block accepted by node!")
                    else:
                        print(f"❌ Block rejected by node: {submit_response.get('message', 'Unknown error')}")

                    await asyncio.sleep(1)

        except websockets.exceptions.ConnectionClosed as e:
            print(f"❌ Connection closed: {e}")
            print(f"   Reconnecting in {MINING_INTERVAL*2}s...")
            await asyncio.sleep(MINING_INTERVAL * 2)
        except ConnectionRefusedError:
            print(f"❌ Connection refused. Is the node running at {NODE_URL}?")
            print(f"   Reconnecting in {MINING_INTERVAL*2}s...")
            await asyncio.sleep(MINING_INTERVAL * 2)
        except Exception as e:
            print(f"❌ Miner error: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(MINING_INTERVAL * 2)

async def main():
    parser = argparse.ArgumentParser(description="PHN Blockchain Miner")
    parser.add_argument('--private_key', '-p', type=str, help='Hex private key string to use for mining')
    parser.add_argument('--generate', '-g', action='store_true', help='Generate a new wallet for mining rewards')
    args = parser.parse_args()

    if args.generate:
        sk, miner_canonical_address = generate_wallet()
        priv_key_hex = sk.to_string().hex()
        print(f"Generated new wallet:")
        print(f" Private Key: {priv_key_hex}")
        print(f" PHN Address: {get_display_address(miner_canonical_address)}")
    elif args.private_key:
        try:
            sk = SigningKey.from_string(bytes.fromhex(args.private_key), curve=SECP256k1)
            miner_canonical_address = sk.get_verifying_key().to_string().hex()
            print(f"Using provided private key. PHN Address: {get_display_address(miner_canonical_address)}")
        except Exception as e:
            print(f"❌ Invalid private key provided: {e}")
            return
    else:
        print("No private key provided and --generate not set. Generating new wallet.")
        sk, miner_canonical_address = generate_wallet()
        priv_key_hex = sk.to_string().hex()
        print(f"Generated new wallet:")
        print(f" Private Key: {priv_key_hex}")
        print(f" PHN Address: {get_display_address(miner_canonical_address)}")

    await mine(miner_canonical_address, sk)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Miner stopped.")
