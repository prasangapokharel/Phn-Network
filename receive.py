from flask import Flask, request, jsonify
import threading
import time
import requests
import hashlib
from datetime import datetime
from pyngrok import ngrok
from blockchain import Blockchain
from wallet import Wallet
from config import NODE_PORT, PEERS, BLOCK_TIME

app = Flask(__name__)

owner_wallet = Wallet.load("wallet.txt")
blockchain = Blockchain(owner_wallet.address)

def broadcast_transaction(tx):
    for peer in PEERS:
        if peer.endswith(f":{NODE_PORT}"):
            continue
        try:
            requests.post(f"{peer}/receive_tx", json=tx)
        except:
            pass

def broadcast_block(block):
    for peer in PEERS:
        if peer.endswith(f":{NODE_PORT}"):
            continue
        try:
            requests.post(f"{peer}/receive_block", json=block.__dict__)
        except:
            pass

@app.route('/balance/<address>', methods=['GET'])
def balance(address):
    return jsonify({"balance": blockchain.get_balance(address)})

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    timestamp = time.time()
    txid_raw = f"{data['sender']}{data['recipient']}{data['amount']}{timestamp}"
    txid = hashlib.sha256(txid_raw.encode()).hexdigest()

    success = blockchain.add_transaction(
        data['sender'], data['sender_pub'], data['signature'],
        data['recipient'], float(data['amount']), txid, timestamp
    )

    if success:
        broadcast_transaction(data)
        block = blockchain.mine_block()
        broadcast_block(block)
        return jsonify({
            "status": "confirmed",
            "block_index": block.index,
            "txid": txid,
            "timestamp": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify({"status": "failed"})

@app.route('/burn', methods=['POST'])
def burn():
    data = request.json
    success = blockchain.burn_tokens(data['holder'], float(data['amount']))
    return jsonify({"status": "confirmed" if success else "failed"})

@app.route('/receive_tx', methods=['POST'])
def receive_tx():
    data = request.json
    blockchain.add_transaction(
        data['sender'], data['sender_pub'], data['signature'],
        data['recipient'], float(data['amount'])
    )
    return jsonify({"status": "received"})

@app.route('/receive_block', methods=['POST'])
def receive_block():
    data = request.json
    if len(blockchain.chain) <= data['index']:
        blockchain.chain.append(data)
        blockchain.pending_transactions.clear()
    return jsonify({"status": "block received"})

@app.route('/mine', methods=['GET'])
def mine():
    block = blockchain.mine_block()
    broadcast_block(block)
    return jsonify({"block": block.__dict__})

def miner_loop():
    while True:
        if blockchain.pending_transactions:
            block = blockchain.mine_block()
            broadcast_block(block)
        time.sleep(BLOCK_TIME)

if __name__ == '__main__':
    threading.Thread(target=miner_loop, daemon=True).start()
    app.run(port=NODE_PORT)
