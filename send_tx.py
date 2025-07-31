import asyncio
import websockets
import json
import time
import hashlib
import sys
from wallet import load_wallet, get_display_address
from config import NODE_PORT

async def send_transaction(node_url, wallet_file, recipient_canonical_address, amount):
    """Send a transaction to the blockchain node."""
    try:
        # Load sender's wallet (load_wallet handles creation if not found/invalid)
        sk, sender_canonical_address = load_wallet(wallet_file)
        print(f"Sending from wallet: {get_display_address(sender_canonical_address)} ({sender_canonical_address[:8]}...)")

        # Validate recipient address format
        if not (isinstance(recipient_canonical_address, str) and len(recipient_canonical_address) == 128 and all(c in '0123456789abcdefABCDEF' for c in recipient_canonical_address)):
             print(f"❌ Recipient address '{recipient_canonical_address}' is not a valid 128-character hexadecimal public key.")
             print("Please provide the full 128-character hexadecimal public key of the recipient.")
             sys.exit(1)
        
        print(f"Sending to: {get_display_address(recipient_canonical_address)} ({recipient_canonical_address[:8]}...)")
        print(f"Amount: {amount} PHN")
        
        # Create transaction message for signing
        timestamp = time.time()
        message_str = f"{sender_canonical_address}{recipient_canonical_address}{amount}{timestamp}"
        message = message_str.encode()
        
        # Sign transaction
        signature = sk.sign(message).hex()
        
        # Create transaction ID
        txid = hashlib.sha256(message).hexdigest()
        
        # Build transaction object (sender and recipient are canonical addresses)
        tx = {
            "sender": sender_canonical_address,
            "recipient": recipient_canonical_address,
            "amount": float(amount),
            "timestamp": timestamp,
            "txid": txid,
            "signature": signature,
        }
        
        print(f"Transaction ID: {txid}")
        print(f"Connecting to node at {node_url}...")
        
        # Send transaction to node
        async with websockets.connect(node_url) as ws:
            # Send transaction
            request = {"type": "send_tx", "tx": tx}
            print(f"Sending request: {request['type']}")
            
            await ws.send(json.dumps(request))
            
            # Wait for response
            response = await ws.recv()
            print(f"Received response: {response}")
            
            response_data = json.loads(response)
            
            if response_data.get("status") == "success":
                print("✅ Transaction sent successfully!")
                print(f"   Message: {response_data.get('message')}")
                print(f"   TX ID: {response_data.get('txid')}")
            else:
                print("❌ Transaction failed!")
                print(f"   Error: {response_data.get('error')}")
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
        print("   The node may have encountered an error.")
    except ConnectionRefusedError:
        print(f"❌ Could not connect to node at {node_url}")
        print("   Make sure the node is running!")
    except Exception as e:
        print(f"❌ Error sending transaction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python send_tx.py <node_ws_url> <wallet_file> <recipient_canonical_address> <amount>")
        print(f"Example: python send_tx.py ws://localhost:{NODE_PORT} companyaccount.txt <128_char_hex_public_key> 100")
        sys.exit(1)
    
    node_url = sys.argv[1]
    wallet_file = sys.argv[2]
    recipient_canonical_address = sys.argv[3] # This is the canonical address
    amount = sys.argv[4]
    
    try:
        amount = float(amount)
        if amount <= 0:
            print("❌ Amount must be positive!")
            sys.exit(1)
    except ValueError:
        print("❌ Invalid amount!")
        sys.exit(1)
    
    asyncio.run(send_transaction(node_url, wallet_file, recipient_canonical_address, amount))
