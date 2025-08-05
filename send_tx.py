import asyncio
import websockets
import json
import time
import hashlib
import sys
from ecdsa import SigningKey, SECP256k1
from wallet import get_display_address  # assuming this is your wallet.py display function
from config import NODE_PORT

DEFAULT_NODE_URL = f"ws://31.97.229.45:{NODE_PORT}"

async def send_transaction(node_url, private_key_hex, recipient_address, amount):
    """Send a transaction to the blockchain node using private key hex."""
    try:
        # Load SigningKey from private key hex
        sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
        # Derive canonical address (public key)
        sender_canonical_address = sk.get_verifying_key().to_string().hex()
        print(f"Sending from wallet: {get_display_address(sender_canonical_address)} ({sender_canonical_address[:8]}...)")

        # Convert recipient address if it's PHN display address
        if recipient_address.startswith("PHN"):
            print("❌ Conversion from PHN address to canonical address is not implemented.")
            print("Please provide full 128-character canonical hex public key as recipient.")
            sys.exit(1)
        else:
            recipient_canonical_address = recipient_address

        # Validate recipient canonical address
        if not (isinstance(recipient_canonical_address, str) and len(recipient_canonical_address) == 128 and all(c in '0123456789abcdefABCDEF' for c in recipient_canonical_address)):
            print("❌ Invalid recipient canonical address format.")
            sys.exit(1)

        print(f"Sending to: {get_display_address(recipient_canonical_address)} ({recipient_canonical_address[:8]}...)")
        print(f"Amount: {amount} PHN")

        timestamp = time.time()
        message_str = f"{sender_canonical_address}{recipient_canonical_address}{amount}{timestamp}"
        message = message_str.encode()

        signature = sk.sign(message).hex()
        txid = hashlib.sha256(message).hexdigest()

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

        async with websockets.connect(node_url) as ws:
            request = {"type": "send_tx", "tx": tx}
            print(f"Sending request: {request['type']}")
            await ws.send(json.dumps(request))

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

    except Exception as e:
        print(f"❌ Error sending transaction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python send_tx.py <node_ws_url|default> <private_key_hex> <recipient_canonical_address> <amount>")
        print(f"Example: python send_tx.py default a3a2858c1ed4ad95fc20e721d9d6963a92aae318065685aac69db4fb26a70c43 380c6104c2e761dcaed07008309e11429918180def901c180e879af9a6d04ff4eed9e83476b5daceeb8f2e575361cfba696a8610cb03a7824e640038ee30056c 12")
        sys.exit(1)

    node_url = sys.argv[1] if sys.argv[1] != "default" else DEFAULT_NODE_URL
    private_key_hex = sys.argv[2]
    recipient_address = sys.argv[3]
    amount = sys.argv[4]

    try:
        amount = float(amount)
        if amount <= 0:
            print("❌ Amount must be positive!")
            sys.exit(1)
    except ValueError:
        print("❌ Invalid amount!")
        sys.exit(1)

    asyncio.run(send_transaction(node_url, private_key_hex, recipient_address, amount))
