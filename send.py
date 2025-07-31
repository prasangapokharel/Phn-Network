import requests
from wallet import Wallet
from ecdsa import SigningKey, SECP256k1
from config import NODE_PORT

def send_phn(recipient, amount, wallet_file="wallet.txt", node_url=f"http://127.0.0.1:{NODE_PORT}"):
    wallet = Wallet.load(wallet_file)
    message = f"{wallet.address}->{recipient}:{amount}"
    signature = wallet.private_key.sign(message.encode()).hex()
    tx = {
        "sender": wallet.address,
        "sender_pub": wallet.public_key.to_string().hex(),
        "signature": signature,
        "recipient": recipient,
        "amount": amount
    }
    resp = requests.post(f"{node_url}/send", json=tx)
    print(resp.json())

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python send.py recipient_address amount")
        exit(1)
    recipient = sys.argv[1]
    amount = float(sys.argv[2])
    send_phn(recipient, amount)
