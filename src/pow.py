from .genesis import hash_block
from .transactions import validate_transaction
from config import DIFFICULTY, BLOCK_REWARD, OWNER_ALLOCATION
from wallet import get_display_address

def validate_block(block, blockchain, owner_address):
    required_fields = ["index", "timestamp", "transactions", "prev_hash", "nonce", "hash"]
    for field in required_fields:
        if field not in block:
            return False, f"Block missing field: {field}"

    if hash_block(block) != block["hash"]:
        return False, "Invalid block hash"

    if not block["hash"].startswith("0" * DIFFICULTY):
        return False, f"Invalid proof of work, must start with {DIFFICULTY} zeros"

    if block["index"] != len(blockchain):
        return False, f"Invalid block index. Expected {len(blockchain)}, got {block['index']}"

    if block["index"] > 0 and block["prev_hash"] != blockchain[-1]["hash"]:
        return False, "Invalid previous hash"

    coinbase_tx_count = 0
    block_reward_sum = 0
    seen_txids = set()

    for tx in block["transactions"]:
        if "txid" not in tx:
            return False, "Transaction missing txid"
        if tx["txid"] in seen_txids:
            return False, "Duplicate txid in block"
        seen_txids.add(tx["txid"])

        if tx["sender"] == "coinbase":
            coinbase_tx_count += 1
            block_reward_sum += tx["amount"]
            if block["index"] == 0:
                if tx["amount"] != OWNER_ALLOCATION or tx["recipient"] != owner_address:
                    return False, "Invalid genesis block reward or recipient"
            else:
                if tx["amount"] != BLOCK_REWARD:
                    return False, "Invalid block reward amount"
            if coinbase_tx_count > 1:
                return False, "Multiple coinbase txs in block"
        else:
            valid, msg = validate_transaction(tx, blockchain)
            if not valid:
                return False, f"Invalid transaction in block: {msg}"

    if coinbase_tx_count != 1:
        return False, "Block must contain exactly one coinbase transaction"

    expected_reward = OWNER_ALLOCATION if block["index"] == 0 else BLOCK_REWARD
    if block_reward_sum != expected_reward:
        return False, "Block reward sum mismatch"

    return True, "Block valid"
