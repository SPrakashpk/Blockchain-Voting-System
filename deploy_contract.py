from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version
import json

# -------------------------
# Configuration
# -------------------------
solc_version = "0.8.0"
GANACHE_URL = "http://127.0.0.1:7545"

# Replace with your real keys
PRIVATE_KEY = "0xe2f9da663f6d03534c85752ef470ea38a2564f7b59e7ea2cd5e165753b262c65"
ACCOUNT = "0xfc207B92b9e01adf4E89cb3ec6d40E4CE190326e"

# -------------------------
# Connect to Ganache
# -------------------------
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
assert w3.is_connected(), "❌ Web3 is not connected."
print("✅ Connected to Ganache")

# -------------------------
# Install and set Solidity compiler
# -------------------------
install_solc(solc_version)
set_solc_version(solc_version)

# -------------------------
# Read and compile Solidity contract
# -------------------------
with open("Voting.sol", "r", encoding='utf-8') as f:
    source_code = f.read()

compiled = compile_source(source_code, output_values=["abi", "bin"])
contract_id, contract_interface = compiled.popitem()

abi = contract_interface['abi']
bytecode = contract_interface['bin']

# -------------------------
# Deploy contract with candidates
# -------------------------
candidate_list = ["ADMK", "DMK", "PMK", "TVK", "BJP"]

Voting = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(ACCOUNT)

tx = Voting.constructor(candidate_list).build_transaction({
    'from': ACCOUNT,
    'nonce': nonce,
    'gas': 6721975,
    'gasPrice': w3.to_wei('1', 'gwei')
})

# -------------------------
# Sign and send transaction
# -------------------------
signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

print("⏳ Deploying contract...")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
contract_address = receipt.contractAddress
print("✅ Contract deployed at:", contract_address)

# -------------------------
# Save ABI and contract address to file
# -------------------------
with open("contract_info.json", "w") as f:
    json.dump({
        "abi": abi,
        "address": contract_address
    }, f)

print("📄 Contract ABI and address saved to contract_info.json")
