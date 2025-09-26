import streamlit as st
import hashlib
import json
import time
import uuid

# ---------------- Blockchain Classes ----------------
class TicketTransaction:
    def __init__(self, tx_type, ticket_id, owner, event=None):
        self.tx_type = tx_type
        self.ticket_id = ticket_id
        self.owner = owner
        self.event = event
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
            return None
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
    def redeem_ticket(self, ticket_id):
        ticket = self.tickets.get(ticket_id)
        if ticket and ticket["status"] == "valid":
            tx = TicketTransaction("redeem", ticket_id, ticket["owner"])
            self.add_transaction(tx)
            ticket["status"] = "redeemed"
            return True
        return False
    def verify_ticket(self, ticket_id):
        return self.tickets.get(ticket_id, None)

# ---------------- Streamlit App ----------------
st.set_page_config(page_title="🎵 Concert Ticketing System", layout="wide", page_icon="🎫")

# ---------------- Session State ----------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = TicketBlockchain()
if "page" not in st.session_state:
    st.session_state.page = 1
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "num_tickets" not in st.session_state:
    st.session_state.num_tickets = 1
if "tickets_booked" not in st.session_state:
    st.session_state.tickets_booked = []
if "redeemed_flag" not in st.session_state:
    st.session_state.redeemed_flag = False

blockchain = st.session_state.blockchain

# ---------------- Events ----------------
events = [
    {"name": "Imagine Dragons Live", "city": "Mumbai", "venue": "NSCI Dome", "time_slots": ["2025-11-09 19:00", "2025-11-10 19:00"], "price": 5999},
    {"name": "Coldplay Concert", "city": "Bengaluru", "venue": "Kanteerava Stadium", "time_slots": ["2025-11-16 20:00", "2025-11-17 20:00"], "price": 5999},
    {"name": "Adele Live", "city": "Delhi", "venue": "Jawaharlal Nehru Stadium", "time_slots": ["2025-12-06 19:30", "2025-12-07 19:30"], "price": 5999},
    {"name": "Ed Sheeran Tour", "city": "Kolkata", "venue": "Salt Lake Stadium", "time_slots": ["2025-12-13 20:00", "2025-12-14 20:00"], "price": 5999},
    {"name": "Arijit Singh Concert", "city": "Pune", "venue": "Shiv Chhatrapati Sports Complex", "time_slots": ["2025-12-20 19:00", "2025-12-21 19:00"], "price": 5999},
]

# ---------------- Styling ----------------
st.markdown("""
    <style>
    .event-box {width: 250px; height: 250px; border-radius:16px; display:flex; justify-content:center; align-items:center; margin:10px; float:left; background-color:#FF6A00; color:black; font-weight:bold; font-size:18px; text-align:center; cursor:pointer;}
    .stButton>button {background-color:#0071e3;color:white;border-radius:8px;padding:10px 20px; font-size:16px;}
    .stTextInput>div>input {padding:10px; border-radius:6px; border:1px solid #ccc;}
    .step-bar {display:flex; justify-content:space-between; margin-bottom:20px;}
    .step {padding:10px 20px; border-radius:8px; color:white;}
    .active {background-color:#0071e3;}
    .inactive {background-color:#a3a3a3;}
    </style>
""", unsafe_allow_html=True)

# ---------------- Step Indicator ----------------
def show_step_indicator(current_page):
    steps = ["1. Select Event", "2. Verify & Redeem", "3. Thank You"]
    st.markdown('<div class="step-bar">', unsafe_allow_html=True)
    for i, step in enumerate(steps, start=1):
        cls = "active" if i == current_page else "inactive"
        st.markdown(f'<div class="step {cls}">{step}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Page 1: Event Selection ----------------
if st.session_state.page == 1:
    show_step_indicator(1)
    st.title("🎵 Select Your Concert Event")
    st.subheader("Step 1: Enter Your Name")
    st.session_state.user_name = st.text_input("Your Name", st.session_state.user_name)

    st.subheader("Step 2: Choose Your Event")
    for i in range(0, len(events), 3):
        cols = st.columns(3)
        for idx, e in enumerate(events[i:i+3]):
            with cols[idx]:
                # Event tile
                if st.button(f"{e['name']}\n{e['city']}\n{e['venue']}\nINR {e['price']}", key=e['name']):
                    st.session_state.selected_event = e

    if st.session_state.selected_event:
        st.subheader("Step 3: Choose Time Slot")
        time_slot = st.selectbox("Select Time Slot", st.session_state.selected_event["time_slots"])
        st.session_state.selected_event["selected_time"] = time_slot

        st.subheader("Step 4: Number of Tickets")
        num_tickets = st.number_input("Select number of tickets", min_value=1, max_value=10, value=1)
        st.session_state.num_tickets = num_tickets

        if st.button("Book Tickets"):
            booked_ids = []
            for _ in range(st.session_state.num_tickets):
                ticket_id = blockchain.issue_ticket(st.session_state.user_name, st.session_state.selected_event)
                booked_ids.append(ticket_id)
            blockchain.mine()
            st.session_state.tickets_booked = booked_ids
            st.session_state.page = 2
            st.experimental_rerun()

# ---------------- Page 2: Ticket Verification & Redemption ----------------
if st.session_state.page == 2:
    show_step_indicator(2)
    st.title("🎫 Verify and Redeem Tickets")

    ticket_id_to_check = st.text_input("Enter Ticket ID to Verify")

    if ticket_id_to_check:
        ticket = blockchain.verify_ticket(ticket_id_to_check)
        if ticket:
            st.success(f"Ticket {ticket_id_to_check} is valid! Owner: {ticket['owner']}")
            st.write(f"Event: {ticket['event']['name']} | Time: {ticket['event']['selected_time']}")
            st.write(f"Status: {ticket['status']}")

            if ticket["status"] == "valid":
                if st.button(f"Redeem Ticket {ticket_id_to_check}"):
                    blockchain.redeem_ticket(ticket_id_to_check)
                    blockchain.mine()
                    st.success(f"Ticket {ticket_id_to_check} redeemed successfully!")
                    st.session_state.redeemed_flag = True

        else:
            st.error("Ticket not found or invalid.")

    # Safe rerun after redemption
    if st.session_state.redeemed_flag:
        st.session_state.redeemed_flag = False
        st.experimental_rerun()

    if st.button("Proceed to Thank You Page"):
        st.session_state.page = 3
        st.experimental_rerun()

# ---------------- Page 3: Thank You ----------------
if st.session_state.page == 3:
    show_step_indicator(3)
    st.title("🎉 Thank You for Booking!")
    st.subheader(f"{st.session_state.user_name}, your tickets are confirmed.")
    st.write("Enjoy the concert! 🎶")
