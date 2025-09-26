"""
📖 Blockchain Ticketing System Demo (Streamlit Cloud Compatible)

- Issue, transfer, redeem, and verify tickets
- Blockchain ledger prevents duplication/fraud
- Demo flow runs automatically at startup
"""

import hashlib
import json
import time
import uuid
from flask import Flask, request, jsonify
from ecdsa import SigningKey, VerifyingKey, NIST384p

# ---------------- Blockchain Classes ----------------
class TicketTransaction:
    def __init__(self, tx_type, ticket_id, owner, event=None, new_owner=None):
        self.tx_type = tx_type
        self.ticket_id = ticket_id
        self.owner = owner
        self.event = event
        self.new_owner = new_owner
        self.timestamp = time.time()

    def to_dict(self):
        return self.__dict__

class Block:
    def __init__(self, index, transactions, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = time.time()
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class TicketBlockchain:
    difficulty = 2

    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.tickets = {}
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def mine(self):
        if not self.pending_transactions:
            return False
        new_block = Block(len(self.chain), self.pending_transactions, self.chain[-1].compute_hash())
        new_block.hash = self.proof_of_work(new_block)
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith("0" * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def issue_ticket(self, owner, event):
        ticket_id = str(uuid.uuid4())
        tx = TicketTransaction("issue", ticket_id, owner, event)
        self.add_transaction(tx)
        self.tickets[ticket_id] = {"owner": owner, "status": "valid", "event": event}
        return ticket_id

    def transfer_ticket(self, ticket_id, new_owner):
        ticket = self.tickets.get(ticket_id)
        if not ticket or ticket["status"] != "valid":
            return False
        tx = TicketTransaction("transfer", ticket_id, ticket["owner"], new_owner=new_owner)
        self.add_transaction(tx)
        ticket["owner"] = new_owner
        return True

    def redeem_ticket(self, ticket_id):
        ticket = self.tickets.get(ticket_id)
        if not ticket or ticket["status"] != "valid":
            return False
        tx = TicketTransaction("redeem", ticket_id, ticket["owner"])
        self.add_transaction(tx)
        ticket["status"] = "redeemed"
        return True

    def verify_ticket(self, ticket_id):
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return None
        return ticket

# ---------------- Flask API ----------------
app = Flask(__name__)
blockchain = TicketBlockchain()

@app.route("/issue", methods=["POST"])
def api_issue():
    data = request.get_json()
    ticket_id = blockchain.issue_ticket(data["owner"], data["event"])
    return jsonify({"ticket_id": ticket_id}), 201

@app.route("/transfer", methods=["POST"])
def api_transfer():
    data = request.get_json()
    success = blockchain.transfer_ticket(data["ticket_id"], data["new_owner"])
    return jsonify({"success": success}), 200

@app.route("/redeem", methods=["POST"])
def api_redeem():
    data = request.get_json()
    success = blockchain.redeem_ticket(data["ticket_id"])
    return jsonify({"success": success}), 200

@app.route("/verify/<ticket_id>", methods=["GET"])
def api_verify(ticket_id):
    ticket = blockchain.verify_ticket(ticket_id)
    if not ticket:
        return jsonify({"valid": False, "message": "Ticket not found"}), 404
    return jsonify({"valid": ticket["status"] == "valid", "ticket": ticket})

@app.route("/mine", methods=["POST"])
def api_mine():
    block = blockchain.mine()
    if not block:
        return jsonify({"message": "No transactions to mine"}), 200
    return jsonify({
        "index": block.index,
        "transactions": [tx.to_dict() for tx in block.transactions],
        "hash": block.hash
    })

@app.route("/chain", methods=["GET"])
def api_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append({
            "index": block.index,
            "transactions": [tx.to_dict() for tx in block.transactions],
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "hash": block.compute_hash()
        })
    return jsonify(chain_data), 200

# ---------------- Demo Flow ----------------
def demo_flow():
    print("\n===== DEMO FLOW =====")
    # 1. Issue ticket
    ticket_id = blockchain.issue_ticket("Alice", "Rock Concert")
    print(f"Issued Ticket ID: {ticket_id} for Alice")

    # 2. Mine block
    block = blockchain.mine()
    print(f"Mined Block Index: {block.index}, Hash: {block.hash}")

    # 3. Transfer ticket
    blockchain.transfer_ticket(ticket_id, "Bob")
    print(f"Transferred Ticket ID: {ticket_id} to Bob")

    # 4. Mine block
    block = blockchain.mine()
    print(f"Mined Block Index: {block.index}, Hash: {block.hash}")

    # 5. Redeem ticket
    blockchain.redeem_ticket(ticket_id)
    print(f"Redeemed Ticket ID: {ticket_id}")

    # 6. Mine block
    block = blockchain.mine()
    print(f"Mined Block Index: {block.index}, Hash: {block.hash}")

    # 7. Verify ticket
    ticket = blockchain.verify_ticket(ticket_id)
    print(f"Ticket Verification: {ticket}\n")

# ---------------- Run Demo & Server ----------------
if __name__ == "__main__":
    demo_flow()
    print("Starting Flask server... Visit http://127.0.0.1:5000 to access API endpoints.")
    app.run(debug=True)
