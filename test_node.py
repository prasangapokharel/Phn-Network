import asyncio
import websockets
import json
from wallet import load_wallet

async def test_node():
    """Test the blockchain node functionality"""
    node_url = "ws://31.97.229.45:8765"
    
    print("🧪 Testing Blockchain Node...")
    print("="*50)
    
    try:
        # Load wallet
        sk, address = load_wallet()
        print(f"📱 Test wallet address: {address}")
        
        # Test connection first
        print("\n🔗 Testing connection...")
        async with websockets.connect(node_url) as ws:
            print("✅ Connected to node!")
            
            # Test 1: Get balance
            print("\n1️⃣ Testing balance check...")
            try:
                await ws.send(json.dumps({"type": "get_balance", "address": address}))
                response = await ws.recv()
                balance_data = json.loads(response)
                
                if "error" in balance_data:
                    print(f"   ❌ Error: {balance_data['error']}")
                else:
                    print(f"   ✅ Balance: {balance_data.get('balance', 'Unknown')} PHN")
            except Exception as e:
                print(f"   ❌ Balance test failed: {e}")
            
            # Test 2: Get blockchain info
            print("\n2️⃣ Testing blockchain info...")
            try:
                await ws.send(json.dumps({"type": "get_blockchain"}))
                response = await ws.recv()
                blockchain_data = json.loads(response)
                
                if "error" in blockchain_data:
                    print(f"   ❌ Error: {blockchain_data['error']}")
                else:
                    print(f"   ✅ Blockchain length: {blockchain_data.get('length', 'Unknown')}")
            except Exception as e:
                print(f"   ❌ Blockchain test failed: {e}")
            
            # Test 3: Get pending transactions
            print("\n3️⃣ Testing pending transactions...")
            try:
                await ws.send(json.dumps({"type": "get_pending"}))
                response = await ws.recv()
                pending_data = json.loads(response)
                
                if "error" in pending_data:
                    print(f"   ❌ Error: {pending_data['error']}")
                else:
                    print(f"   ✅ Pending transactions: {pending_data.get('count', 'Unknown')}")
            except Exception as e:
                print(f"   ❌ Pending test failed: {e}")
            
            # Test 4: Send a test transaction (to self)
            print("\n4️⃣ Testing transaction sending...")
            try:
                import time
                import hashlib
                
                timestamp = time.time()
                amount = 1.0
                message = f"{address}{address}{amount}{timestamp}".encode()
                signature = sk.sign(message).hex()
                txid = hashlib.sha256(message).hexdigest()
                
                tx = {
                    "sender": address,
                    "recipient": address,  # Send to self
                    "amount": amount,
                    "timestamp": timestamp,
                    "txid": txid,
                    "signature": signature,
                }
                
                await ws.send(json.dumps({"type": "send_tx", "tx": tx}))
                response = await ws.recv()
                tx_data = json.loads(response)
                
                if tx_data.get("status") == "success":
                    print("   ✅ Test transaction successful!")
                    print(f"   TX ID: {tx_data.get('txid', 'Unknown')}")
                else:
                    print(f"   ❌ Test transaction failed: {tx_data.get('error', 'Unknown')}")
            except Exception as e:
                print(f"   ❌ Transaction test failed: {e}")
            
            print("\n🎉 All tests completed!")
            
    except ConnectionRefusedError:
        print("❌ Could not connect to node!")
        print("   Make sure the node is running with: python p2p_node.py")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
        print("   The node may have encountered an error.")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_node())
