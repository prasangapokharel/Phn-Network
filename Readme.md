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
python scripts/owner.py
```

### Step 2: Start the Blockchain Node
Start the core node to manage the blockchain and process transactions.

```bash
start.bat
```

*Alternatively, run manually:*
```bash
python scripts/p2p_node.py
```

### Step 3: Start Mining
Start a miner to create new blocks and earn rewards. Use a new wallet or an existing one.

```bash
mining.bat
```

*Alternatively, run manually:*
- With a new wallet (saved to `mined.txt`):
  ```bash
  python scripts/miner.py --generate
  ```
- With an existing wallet (e.g., `owner.txt`):
  ```bash
  python scripts/miner.py --wallet owner.txt
  ```

### Step 4: Interact with the Network
- **Send Transactions**:
  ```bash
  python scripts/send_tx.py ws://localhost:8765 <sender_wallet_file> <recipient_canonical_address> <amount>
  ```
  Example:
  ```bash
  python scripts/send_tx.py ws://localhost:8765 owner.txt 380c6104c2e761dcaed07008309e11429918180def901c180e879af9a6d04ff4eed9e83476b5daceeb8f2e575361cfba696a8610cb03a7824e640038ee30056c 500
  ```

- **Check Balance**:
  ```bash
  python scripts/check_balance.py ws://localhost:8765 <canonical_address>
  ```
  Example:
  ```bash
  python scripts/check_balance.py ws://localhost:8765 380c6104c2e761dcaed07008309e11429918180def901c180e879af9a6d04ff4eed9e83476b5daceeb8f2e575361cfba696a8610cb03a7824e640038ee30056c
  ```

- **Interactive Client**:
  ```bash
  python scripts/blockchain_client.py
  ```

- **Generate New Wallet**:
  ```bash
  python scripts/wallet.py
  ```

## Key Files
- **`owner.txt`**: Stores the owner's private key and canonical address. **Keep secure!**
- **`wallet.txt` / `mined.txt`**: Stores user or miner keys and addresses.
- **`blockchain.json`**: Stores the blockchain history. **Do not manually edit.**

## Running the Network (Step-by-Step)

1. Run `python scripts/owner.py` to initialize the owner wallet.
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