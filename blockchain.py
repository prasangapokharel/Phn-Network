import hashlib
import json
import time
from collections import deque
from ecdsa import VerifyingKey, SECP256k1

TOTAL_SUPPLY = 100_000_000
OWNER_SHARE = 0.10
TX_FEE = 0.001

class Block:
    def __init__(self, index, transactions, timestamp, prev_hash, validator):
        self.index = index
        self.transactions = transactions  # list of dicts
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.validator = validator
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "validator": self.validator
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self, owner_address):
        self.chain = []
        self.pending_transactions = deque()
        self.total_supply = TOTAL_SUPPLY
        self.owner = owner_address
        self.balances = {self.owner: TOTAL_SUPPLY * OWNER_SHARE}
        self.burned_supply = 0
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0", "system")
        self.chain.append(genesis_block)

    def get_balance(self, address):
        return self.balances.get(address, 0)

    def verify_signature(self, sender_pub_hex, signature_hex, message):
        try:
            vk = VerifyingKey.from_string(bytes.fromhex(sender_pub_hex), curve=SECP256k1)
            vk.verify(bytes.fromhex(signature_hex), message.encode())
            return True
        except Exception:
            return False

    def add_transaction(self, sender, sender_pub, signature, recipient, amount, txid=None, timestamp=None):
        # Verify signature
        msg = f"{sender}{recipient}{amount}"
        if not self.verify_signature(sender_pub, signature, msg):
            return False, "Invalid signature"

        if self.get_balance(sender) < amount + TX_FEE:
            return False, "Insufficient balance"

        tx = {
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "txid": txid or hashlib.sha256(f"{sender}{recipient}{amount}{time.time()}".encode()).hexdigest(),
            "timestamp": timestamp or time.time()
        }
        self.pending_transactions.append(tx)
        return True, "Transaction added"

    def mine_block(self):
        if not self.pending_transactions:
            return None
        last_block = self.chain[-1]
        block = Block(
            index=last_block.index + 1,
            transactions=list(self.pending_transactions),
            timestamp=time.time(),
            prev_hash=last_block.hash,
            validator=self.owner
        )
        # Update balances
        for tx in block.transactions:
            sender = tx["sender"]
            recipient = tx["recipient"]
            amount = tx["amount"]
            self.balances[sender] = self.balances.get(sender, 0) - amount - TX_FEE
            self.balances[recipient] = self.balances.get(recipient, 0) + amount
            # Fee goes to owner (miner)
            self.balances[self.owner] = self.balances.get(self.owner, 0) + TX_FEE
        self.chain.append(block)
        self.pending_transactions.clear()
        return block
