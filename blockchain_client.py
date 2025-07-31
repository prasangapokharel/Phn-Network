import asyncio
import websockets
import json
from wallet import load_wallet

class BlockchainClient:
    def __init__(self, node_url="ws://localhost:8765"):
        self.node_url = node_url
        self.wallet_file = "wallet.txt"
    
    async def connect(self):
        """Connect to the blockchain node"""
        try:
            self.ws = await websockets.connect(self.node_url)
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the node"""
        if hasattr(self, 'ws'):
            await self.ws.close()
    
    async def send_request(self, request):
        """Send request to node and get response"""
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        return json.loads(response)
    
    async def get_balance(self, address):
        """Get balance for address"""
        request = {"type": "get_balance", "address": address}
        response = await self.send_request(request)
        return response.get("balance", 0)
    
    async def send_transaction(self, recipient, amount):
        """Send transaction"""
        sk, sender = load_wallet(self.wallet_file)
        
        import time
        import hashlib
        
        timestamp = time.time()
        message = f"{sender}{recipient}{amount}{timestamp}".encode()
        signature = sk.sign(message).hex()
        txid = hashlib.sha256(message).hexdigest()
        
        tx = {
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "timestamp": timestamp,
            "txid": txid,
            "signature": signature,
        }
        
        request = {"type": "send_tx", "tx": tx}
        response = await self.send_request(request)
        return response
    
    async def get_blockchain_info(self):
        """Get blockchain information"""
        request = {"type": "get_blockchain"}
        return await self.send_request(request)

async def interactive_client():
    """Interactive blockchain client"""
    client = BlockchainClient()
    
    if not await client.connect():
        print("❌ Could not connect to blockchain node!")
        return
    
    print("🚀 Connected to blockchain node!")
    
    # Load wallet info
    try:
        sk, address = load_wallet()
        print(f"📱 Your address: {address}")
        
        # Check balance
        balance = await client.get_balance(address)
        print(f"💰 Your balance: {balance} PHN")
        
    except Exception as e:
        print(f"❌ Wallet error: {e}")
        await client.disconnect()
        return
    
    while True:
        print("\n" + "="*50)
        print("🔗 Blockchain Client Menu:")
        print("1. Check balance")
        print("2. Send transaction")
        print("3. View blockchain info")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        try:
            if choice == "1":
                addr = input("Enter address (or press Enter for your address): ").strip()
                if not addr:
                    addr = address
                balance = await client.get_balance(addr)
                print(f"💰 Balance of {addr}: {balance} PHN")
            
            elif choice == "2":
                recipient = input("Enter recipient address: ").strip()
                amount = float(input("Enter amount: ").strip())
                
                if amount <= 0:
                    print("❌ Amount must be positive!")
                    continue
                
                print("Sending transaction...")
                response = await client.send_transaction(recipient, amount)
                
                if response.get("status") == "success":
                    print("✅ Transaction sent successfully!")
                    print(f"TX ID: {response.get('txid')}")
                else:
                    print(f"❌ Transaction failed: {response.get('error')}")
            
            elif choice == "3":
                info = await client.get_blockchain_info()
                print(f"📊 Blockchain has {info.get('length', 0)} blocks")
                
                # Show recent blocks
                blockchain = info.get('blockchain', [])
                if blockchain:
                    print("\n📦 Recent blocks:")
                    for block in blockchain[-3:]:  # Show last 3 blocks
                        print(f"   Block #{block['index']}: {len(block['transactions'])} transactions")
            
            elif choice == "4":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice!")
                
        except ValueError:
            print("❌ Invalid input!")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(interactive_client())
