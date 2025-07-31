# PHN Blockchain Network

A simple peer-to-peer blockchain implementation with a custom token (PHN), Proof-of-Work mining, and persistent storage. This project demonstrates core blockchain concepts in Python.

## Features

*   **Custom PHN Token:** A native cryptocurrency for the network.
*   **Proof-of-Work (PoW) Mining:** Blocks are added to the chain by miners solving a cryptographic puzzle.
*   **Owner Allocation at Genesis:** A predefined percentage of the total supply is allocated to a designated owner at the very first block.
*   **Persistent Blockchain Storage:** The entire blockchain state is saved to `blockchain.json` and loaded on startup, ensuring data is not lost when the node is shut down.
*   **Cryptographic Signatures (ECDSA):** Transactions are secured using elliptic curve digital signatures.
*   **Canonical and Display Addresses:**
    *   **Canonical Address:** The raw 128-character hexadecimal public key, used internally for all cryptographic operations and transaction processing.
    *   **Display Address:** A human-readable `PHN` prefixed address derived from the canonical address, used for user-friendly viewing and sharing.
*   **Basic Peer-to-Peer Communication:** Nodes and clients communicate via WebSockets.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.x** (3.8 or newer recommended)
*   **pip** (Python package installer, usually comes with Python)

## Setup

1.  **Navigate to the project directory:**
    \`\`\`bash
    cd Phn-Network/scripts
    \`\`\`

2.  **Install Python dependencies:**
    \`\`\`bash
    pip install -r requirements.txt
    \`\`\`

## Key Concepts

*   **`owner.txt`:** This file stores the private key and canonical address of the designated owner of the blockchain. It's crucial for the initial token allocation. **Keep this file secure!**
*   **`wallet.txt` / `mined.txt`:** These files store private keys and canonical addresses for regular users or miners.
*   **`blockchain.json`:** This file stores the entire history of the blockchain. It's automatically created and updated by the `p2p_node.py`. **Do not manually edit this file.**

## Usage (Commands)

All commands should be run from the `scripts/` directory.

### 1. Initialize Owner Wallet

This script generates or loads the owner's wallet and saves it to `owner.txt`. This wallet will receive the initial PHN allocation at genesis. **Run this FIRST, before starting the node.**

\`\`\`bash
python owner.py
\`\`\`

### 2. Start the Blockchain Node

This is the core of the network. It manages the blockchain, processes transactions, and communicates with miners and clients. **At least one node must be running for the network to function.**

\`\`\`bash
python p2p_node.py
\`\`\`

### 3. Start a Miner

Miners create new blocks by solving Proof-of-Work puzzles and include pending transactions. They receive `BLOCK_REWARD` for each successful block.

*   **Start with a new wallet for mining rewards (saved to `mined.txt`):**
    \`\`\`bash
    python miner.py --generate
    # or
    python miner.py -g
    \`\`\`

*   **Start with an existing wallet (e.g., your `owner.txt` or a specific `wallet.txt`):**
    \`\`\`bash
    python miner.py --wallet owner.txt
    # or
    python miner.py -w my_other_wallet.txt
    \`\`\`

*   **Start with the default `wallet.txt` (if no arguments are given):**
    \`\`\`bash
    python miner.py
    \`\`\`

### 4. Send Transactions

Send PHN tokens from one address to another. You need the **128-character canonical public key** of the recipient.

\`\`\`bash
python send_tx.py <node_ws_url> <sender_wallet_file> <recipient_canonical_address> <amount>
\`\`\`

*   `<node_ws_url>`: E.g., `ws://localhost:8765`
*   `<sender_wallet_file>`: E.g., `owner.txt` or `wallet.txt`
*   `<recipient_canonical_address>`: The 128-character hex public key of the recipient.
*   `<amount>`: The amount of PHN to send (e.g., `100`, `0.5`).

**Example:**
\`\`\`bash
python send_tx.py ws://localhost:8765 owner.txt 380c6104c2e761dcaed07008309e11429918180def901c180e879af9a6d04ff4eed9e83476b5daceeb8f2e575361cfba696a8610cb03a7824e640038ee30056c 500
\`\`\`

### 5. Check Balances & Node Info

Query the node for an address's balance or general blockchain information.

*   **Check balance of a specific canonical address:**
    \`\`\`bash
    python check_balance.py <node_ws_url> <canonical_address>
    \`\`\`
    **Example:**
    \`\`\`bash
    python check_balance.py ws://localhost:8765 380c6104c2e761dcaed07008309e11429918180def901c180e879af9a6d04ff4eed9e83476b5daceeb8f2e575361cfba696a8610cb03a7824e640038ee30056c
    \`\`\`

*   **Get general node/blockchain info (if no address is provided):**
    \`\`\`bash
    python check_balance.py <node_ws_url>
    \`\`\`
    **Example:**
    \`\`\`bash
    python check_balance.py ws://localhost:8765
    \`\`\`

### 6. Interactive Blockchain Client

A simple command-line interface to interact with the blockchain node (check balance, send transactions, view info).

\`\`\`bash
python blockchain_client.py
\`\`\`

### 7. Wallet Generation (Utility)

Generate a new wallet (private key and canonical address) and save it to `wallet.txt`. This is primarily used by `miner.py` and `blockchain_client.py` if no wallet is found.

\`\`\`bash
python wallet.py
\`\`\`

### 8. Debugging Tron Contracts (External)

These scripts are for interacting with the Tron network and are separate from the PHN blockchain.

*   **Main contract interaction:**
    \`\`\`bash
    python contracts.py
    \`\`\`

*   **Debugging Tron transactions/contracts:**
    \`\`\`bash
    python debug-contracts.py
    \`\`\`

*   **Fixing Tron contract issues:**
    \`\`\`bash
    python fix-contracts.py
    \`\`\`

### 9. Testing the Node (Utility)

A script to perform basic tests on the running `p2p_node.py`.

\`\`\`bash
python test_node.py
\`\`\`

## Running the Network (Step-by-Step)

To get your PHN Blockchain up and running:

1.  **Initialize Owner:** Open a terminal, navigate to `scripts/`, and run `python owner.py`. Copy the canonical address.
2.  **Start Node:** Open a **new** terminal, navigate to `scripts/`, and run `python p2p_node.py`.
3.  **Start Miner:** Open a **new** terminal, navigate to `scripts/`, and run `python miner.py --generate` (or `--wallet` with an existing file).
4.  **Interact:** Use `send_tx.py`, `check_balance.py`, or `blockchain_client.py` in other terminals to send transactions and query the network.

Remember to keep the `p2p_node.py` terminal open for the network to remain active.

## Troubleshooting

*   **"Connection refused"**: Ensure `p2p_node.py` is running before trying to connect with other scripts.
*   **Balance not updating**: Make sure a `miner.py` is running and successfully mining blocks. Transactions only update balances once they are included in a mined block.
*   **Node resets to 10M PHN on restart**: This means `blockchain.json` was not loaded or was invalid. Ensure `p2p_node.py` is shut down gracefully (Ctrl+C) to save the chain, or check for errors during loading. If you want a fresh start, delete `blockchain.json`.

## Future Enhancements

*   Peer discovery and synchronization for a truly decentralized network.
*   Transaction fees.
*   More robust error handling and logging.
*   A simple web-based block explorer.
*   Command-line interface for wallet management.

\`\`\`
