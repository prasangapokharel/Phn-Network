import time
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
from wallet import get_display_address
import hashlib

# The blockchain is expected to be passed in or imported to check balances/validation
# For example, you can import blockchain from genesis.py or pass as parameter

def get_balance(address, blockchain):
    balance = 0
    for block in blockchain:
        for tx in block["transactions"]:
            if tx["sender"] == address:
                balance -= tx["amount"]
            if tx["recipient"] == address:
                balance += tx["amount"]
    return balance

def verify_signature(tx):
    if tx["sender"] == "coinbase":
        return True
    try:
        signature = bytes.fromhex(tx["signature"])
        sender_vk = VerifyingKey.from_string(bytes.fromhex(tx["sender"]), curve=SECP256k1)
        message = f"{tx['sender']}{tx['recipient']}{tx['amount']}{tx['timestamp']}".encode()
        return sender_vk.verify(signature, message)
    except (BadSignatureError, Exception) as e:
        print(f"Signature verification failed for TX {tx.get('txid', 'N/A')}: {e}")
        return False

def validate_transaction(tx, blockchain):
    required_fields = ["sender", "recipient", "amount", "timestamp", "signature"]
    for field in required_fields:
        if field not in tx:
            return False, f"Missing field: {field}"

    if tx["amount"] <= 0:
        return False, "Amount must be positive"

    if tx["sender"] != "coinbase":
        sender_balance = get_balance(tx["sender"], blockchain)
        if sender_balance < tx["amount"]:
            return False, "Insufficient balance"

    if not verify_signature(tx):
        return False, "Invalid signature"

    return True, "Valid transaction"
