import asyncio
import websockets
import json
import sys
from wallet import get_display_address
from config import NODE_PORT

async def check_balance(node_url, canonical_address):
    """Check balance of an address.
    'canonical_address' is the raw public key hex."""
    try:
        print(f"Checking balance for: {get_display_address(canonical_address)} ({canonical_address[:8]}...)")
        print(f"Connecting to node: {node_url}")
        
        async with websockets.connect(node_url) as ws:
            # Send balance request (using canonical address)
            request = {"type": "get_balance", "address": canonical_address}
            print(f"Sending request: {request}")
            
            await ws.send(json.dumps(request))
            
            # Wait for response
            response = await ws.recv()
            print(f"Received response: {response}")
            
            data = json.loads(response)
            
            if "balance" in data:
                balance = data["balance"]
                # Display the balance with the PHN format address
                print(f"✅ Balance of {data.get('display_address', canonical_address)}: {balance} PHN")
                return balance
            else:
                print(f"❌ Error: {data.get('error', 'Unknown error')}")
                return None
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
        print("   The node may have encountered an error.")
    except ConnectionRefusedError:
        print(f"❌ Could not connect to node at {node_url}")
        print("   Make sure the node is running!")
    except Exception as e:
        print(f"❌ Error checking balance: {e}")
        return None

async def get_node_info(node_url):
    """Get blockchain information from node"""
    try:
        print(f"Getting node info from: {node_url}")
        
        async with websockets.connect(node_url) as ws:
            # Get blockchain info
            await ws.send(json.dumps({"type": "get_blockchain"}))
            response = await ws.recv()
            blockchain_data = json.loads(response)
            
            # Get pending transactions
            await ws.send(json.dumps({"type": "get_pending"}))
            response = await ws.recv()
            pending_data = json.loads(response)
            
            print(f"📊 Blockchain Info:")
            print(f"   Blocks: {blockchain_data.get('length', 0)}")
            print(f"   Pending TXs: {pending_data.get('count', 0)}")
            
            return True
            
    except Exception as e:
        print(f"Could not get node info: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_balance.py <node_ws_url> [canonical_address]")
        print(f"Example: python check_balance.py ws://localhost:{NODE_PORT} <your_128_char_hex_public_key>")
        print("If no address provided, will show node info only")
        sys.exit(1)
    
    node_url = sys.argv[1]
    
    if len(sys.argv) >= 3:
        address_input = sys.argv[2]
        # Basic validation for canonical address format
        if not (isinstance(address_input, str) and len(address_input) == 128 and all(c in '0123456789abcdefABCDEF' for c in address_input)):
            print(f"❌ Provided address '{address_input}' is not a valid 128-character hexadecimal public key.")
            sys.exit(1)
        asyncio.run(check_balance(node_url, address_input))
    else:
        asyncio.run(get_node_info(node_url))
