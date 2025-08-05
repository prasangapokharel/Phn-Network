import asyncio
import websockets
import json
import sys

NODE_URL = "ws://31.97.229.45:8765"

async def check_balance(node_url, canonical_address):
    try:
        async with websockets.connect(node_url) as ws:
            # Request balance for the address
            request = {"type": "get_balance", "address": canonical_address}
            await ws.send(json.dumps(request))
            response = await ws.recv()
            data = json.loads(response)
            
            if "balance" in data:
                print(f"Balance for address {canonical_address[:8]}...: {data['balance']} PHN")
            else:
                print(f"Failed to get balance: {data}")
    except Exception as e:
        print(f"Error checking balance: {e}")

if __name__ == "__main__":
    address = "PHNc23f3f4b493f342a19d88167ea98d54ddd99a47e"
    asyncio.run(check_balance(NODE_URL, address))
