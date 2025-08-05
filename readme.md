# PHN Blockchain Network

A simple peer-to-peer blockchain implementation with a custom token (PHN), Proof-of-Work mining, and persistent storage. This project demonstrates core blockchain concepts using Python.

## Features

- **Custom PHN Token**: Native cryptocurrency for the network.
- **Proof-of-Work (PoW) Mining**: Miners solve cryptographic puzzles to add blocks.
- **Owner Allocation at Genesis**: Predefined percentage of total supply allocated to the owner at the genesis block.
- **Persistent Storage**: Blockchain state saved to `blockchain.json` for data persistence.
- **Cryptographic Signatures**: Transactions secured with ECDSA.
- **Canonical & Display Addresses**:
  - **Canonical Address**: 128-character hex public key for cryptographic operations.
  - **Display Address**: Human-readable `PHN` prefixed address for user-friendly interaction.
- **Peer-to-Peer Communication**: Nodes and clients communicate via WebSockets.

## Prerequisites

- **Python 3.x** (3.8 or newer recommended)
- **pip** (Python package installer, usually included with Python)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/phn-blockchain.git
   cd phn-blockchain
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

All commands should be run from the project root directory. Ensure `p2p_node.py` is running before executing other scripts.

### Step 1: Initialize Owner Wallet
Run this first to generate or load the owner's wallet, which receives the initial PHN allocation.

```bash
python owner.py
```

### Step 2: Start the Blockchain Node
Start the core node to manage the blockchain and process transactions.

```bash
start.bat
```

*Alternatively, run manually:*
```bash
python p2p_node.py
```

### Step 3: Start Mining
Start a miner to create new blocks and earn rewards. Use a new wallet or an existing one.

```bash
mining.bat
```

*Alternatively, run manually:*
- With a new wallet (saved to `mined.txt`):
  ```bash
  python miner.py --generate
  ```
- With an existing wallet (e.g., `private_key`):
  ```bash
  python miner.py --wallet private_key
  ```

### Step 4: Interact with the Network
- **Send Transactions**:
  ```bash
  python send_tx.py ws://31.97.229.45:8765 <sender_wallet_file> <recipient_canonical_address> <amount>
  ```
  Example:
  ```bash
  python send_tx.py ws://31.97.229.45:8765 <private key> 44d5b083f14cb7fc532ef394438e4606de6ddb7dd2db6b35a40d2fd99e8e2b3635dba575aaa59ad0c4e5400f3b1f021ae2bf1632daa9d6a86d8914faff42416a 1

  ```

- **Check Balance**:
  ```bash
  python check_balance.py ws://31.97.229.45:8765 bd4a8333ad5e46c0c8f9863ddce4f0ef687f0372fa82268e7b084215c49ab815193adc5460d38b21b20da8f0a89b066a4daa3c452f9b54947ca5e59b29cc0724
  ```
  Example:
  ```bash
  python check_balance.py ws://31.97.229.45:8765 286bd8dd4f035ef0e89e413002d9aca33a2c7c694dfd79e9f2297200b496e928d4e91ffb93c0b30413222e60cc3bd3b68d7e2d15a5ad656c90fd27a3bab7e54e
  ```

- **Interactive Client**:
  ```bash
  python blockchain_client.py
  ```

- **Generate New Wallet**:
  ```bash
  python wallet.py
  ```

## Key Files
- **`private_key`**: Stores the owner's private key and canonical address. **Keep secure!**
- **`wallet.txt` / `mined.txt`**: Stores user or miner keys and addresses.
- **`blockchain.json`**: Stores the blockchain history. **Do not manually edit.**

## Running the Network (Step-by-Step)

1. Run `python owner.py` to initialize the owner wallet.
2. Open a new terminal and run `start.bat` to start the node.
3. Open another terminal and run `mining.bat` to start mining.
4. Use `send_tx.py`, `check_balance.py`, or `blockchain_client.py` to interact with the network.

Keep the node (`start.bat`) running for the network to function.

## Troubleshooting

- **"Connection refused"**: Ensure `start.bat` or `p2p_node.py` is running.
- **Balance not updating**: Ensure a miner is running (`mining.bat`) to include transactions in blocks.
- **Node resets to 10M PHN**: Check if `blockchain.json` is valid or was deleted. Shut down `p2p_node.py` gracefully (Ctrl+C) to save the chain.

## Future Enhancements

- Peer discovery and synchronization.
- Transaction fees.
- Enhanced error handling and logging.
- Web-based block explorer.
- Wallet management CLI.