import asyncio
import websockets
import json
import hashlib
import time
from ecdsa import SigningKey, SECP256k1

# -------------------------
# Utility: Address Conversion
# -------------------------
def get_display_address(canonical_public_key_hex):
    """Convert canonical public key hex to PHN address."""
    public_key_bytes = bytes.fromhex(canonical_public_key_hex)
    address_hash = hashlib.sha256(public_key_bytes).hexdigest()[:40]
    return f"PHN{address_hash}"

def canonical_from_display(display_address):
    """Placeholder for PHN -> Canonical conversion."""
    if display_address.startswith("PHN"):
        raise NotImplementedError("PHN to canonical conversion not implemented. Use canonical hex for now.")
    return display_address

# -------------------------
# Blockchain Client
# -------------------------
class BlockchainClient:
    def __init__(self, node_url="ws://31.97.229.45:8765"):
        self.node_url = node_url
    
    async def connect(self):
        """Reconnect every time to avoid ping timeout."""
        self.ws = await websockets.connect(
            self.node_url,
            ping_interval=None,   # disable auto ping
            ping_timeout=None
        )

    async def disconnect(self):
        """Close WebSocket."""
        if hasattr(self, 'ws'):
            await self.ws.close()

    async def send_request(self, request):
        """Send JSON request and wait for response."""
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        return json.loads(response)

    async def get_balance(self, address):
        """Fetch balance of an address."""
        await self.connect()
        request = {"type": "get_balance", "address": address}
        response = await self.send_request(request)
        await self.disconnect()
        return response.get("balance", 0)

    async def send_transaction(self, sk, sender_address, recipient, amount):
        """Send signed transaction."""
        await self.connect()

        # PHN → Canonical conversion if needed
        if recipient.startswith("PHN"):
            try:
                recipient = canonical_from_display(recipient)
            except NotImplementedError:
                print("❌ PHN to canonical conversion not implemented. Use canonical hex.")
                await self.disconnect()
                return {"status": "error", "error": "Invalid recipient address"}

        timestamp = time.time()
        message = f"{sender_address}{recipient}{amount}{timestamp}".encode()
        signature = sk.sign(message).hex()
        txid = hashlib.sha256(message).hexdigest()

        tx = {
            "sender": sender_address,
            "recipient": recipient,
            "amount": amount,
            "timestamp": timestamp,
            "txid": txid,
            "signature": signature,
        }

        request = {"type": "send_tx", "tx": tx}
        response = await self.send_request(request)
        await self.disconnect()
        return response

    async def get_blockchain_info(self):
        """Get blockchain summary."""
        await self.connect()
        request = {"type": "get_blockchain"}
        response = await self.send_request(request)
        await self.disconnect()
        return response

# -------------------------
# Interactive CLI
# -------------------------
async def interactive_client():
    client = BlockchainClient()

    # Input private key
    sk_hex = input("🔑 Enter your Private Key (hex): ").strip()
    try:
        sk = SigningKey.from_string(bytes.fromhex(sk_hex), curve=SECP256k1)
    except Exception:
        print("❌ Invalid private key format!")
        return

    sender_canonical = sk.get_verifying_key().to_string().hex()
    sender_display = get_display_address(sender_canonical)

    print(f"📱 Your PHN Address: {sender_display}")

    # Show initial balance
    balance = await client.get_balance(sender_canonical)
    print(f"💰 Your Balance: {balance} PHN")

    while True:
        print("\n" + "=" * 50)
        print("🔗 Blockchain Client Menu:")
        print("1. Check balance")
        print("2. Send transaction")
        print("3. View blockchain info")
        print("4. Exit")

        choice = input("\nEnter choice (1-4): ").strip()

        try:
            if choice == "1":
                addr = input("Enter address (Press Enter for your address): ").strip()
                if not addr:
                    addr = sender_canonical
                bal = await client.get_balance(addr)
                print(f"💰 Balance of {addr}: {bal} PHN")

            elif choice == "2":
                recipient = input("Enter recipient address (PHN or canonical): ").strip()
                amount = float(input("Enter amount: ").strip())
                if amount <= 0:
                    print("❌ Amount must be positive!")
                    continue
                print("🚀 Sending transaction...")
                response = await client.send_transaction(sk, sender_canonical, recipient, amount)
                if response.get("status") == "success":
                    print(f"✅ TX sent! TXID: {response.get('txid')}")
                else:
                    print(f"❌ TX failed: {response.get('error')}")

            elif choice == "3":
                info = await client.get_blockchain_info()
                print(f"📊 Blockchain Height: {info.get('length', 0)} blocks")
                for block in info.get('blockchain', [])[-3:]:
                    print(f"   Block #{block['index']}: {len(block['transactions'])} TXs")

            elif choice == "4":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice!")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(interactive_client())
