Got it ✅
I’ll update your **README.md** so that it includes **clear CMD commands** to:

* Generate a wallet
* Send PHN transactions
* Mine PHN
* Check balance

Here’s the improved `README.md`:

---

````markdown
# 🚀 PHN Blockchain (Open Source)

Welcome to the **PHN Blockchain** open-source project.  
This repository allows anyone to:
- ✅ Generate their own **PHN wallet**
- ✅ Mine PHN tokens (`miner.py`)
- ✅ Check balances, send transactions (`blockchain_client.py`)
- ✅ Connect to the public node or your own node

---

## 📦 Requirements
Make sure you have:
- Python **3.10+**
- `pip` package manager

---

## ⚡ Installation

```bash
# Clone the repository
git clone https://github.com/prasangapokharel/Phn-Network
cd PHN-Blockchain

# Install dependencies
pip install -r requirements.txt
````

---

## 🔑 1. Generate a Wallet

Run this command in CMD to create your wallet:

```bash
python blockchain_client.py
```

* It will ask for your **Private Key** (leave blank to auto-generate one)
* Output example:

```
🔑 Private Key: <save this safely>
📱 PHN Address: PHNxxxxxxxxxxxxxxxxxxxx
💰 Balance: 0 PHN
```

⚠️ **Save your private key** securely. Losing it means losing your PHN.

---

## 💸 2. Send PHN

To send PHN to another wallet:

```bash
python blockchain_client.py
```

* Select option `2` (**Send transaction**)
* Enter:

  * **Recipient Address** (PHN or canonical address)
  * **Amount**

Example:

```
Enter recipient address: PHNc23f3f4b493f342a19d88167ea98d54ddd99a47e
Enter amount: 10
✅ Transaction sent successfully!
```

---

## ⛏ 3. Start Mining PHN

Run the miner to start mining:

```bash
python miner.py
```

* Connects to the PHN node
* Mines blocks and rewards go to your wallet address

---

## 💰 4. Check Balance

You can check your balance via:

```bash
python blockchain_client.py
```

* Choose option `1` (**Check balance**)

Or directly from CMD (using canonical address):

```bash
python check_balance.py ws://31.97.229.45:8765 <Your_Canonical_Address>
```

---

## 🌍 Public Node Connection

Use the PHN Public Node:

```
ws://31.97.229.45:8765
```

Or run your own node locally:

```
ws://localhost:8765
```

---

## ⚠️ Security Notes

* **Never share your private key**
* `.env`, `wallet.txt`, `owner.txt` are ignored in `.gitignore`
* Only `miner.py` and `blockchain_client.py` are safe for public

---

## 📄 License

Open-source for everyone to mine, send, and build on PHN.

---

### 🤝 Contributing

Pull requests are welcome!
Fork → Improve → Submit PR

````

---

