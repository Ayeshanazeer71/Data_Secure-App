import streamlit as st
import hashlib
import json
import os
import time
from cryptography.fernet import Fernet

# Paths
DATA_FILE = "data_store.json"
ATTEMPTS_FILE = "attempts.json"
KEY_FILE = "fernet.key"

# Generate/load encryption key
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as f:
        KEY = f.read()
else:
    KEY = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(KEY)

cipher = Fernet(KEY)

# Load stored data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        stored_data = json.load(f)
else:
    stored_data = {}

# Load failed attempts
if os.path.exists(ATTEMPTS_FILE):
    with open(ATTEMPTS_FILE, "r") as f:
        attempt_data = json.load(f)
else:
    attempt_data = {}

# Save data
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(stored_data, f)

def save_attempts():
    with open(ATTEMPTS_FILE, "w") as f:
        json.dump(attempt_data, f)

# Hash passkey
def hash_passkey(passkey):
    return hashlib.sha256(passkey.encode()).hexdigest()

# Lock checker
def is_locked(code):
    info = attempt_data.get(code, {"attempts": 0, "lock_time": 0})
    if info["attempts"] < 3:
        return False
    # Check if 5 minutes passed
    if time.time() - info["lock_time"] >= 300:
        attempt_data[code] = {"attempts": 0, "lock_time": 0}
        save_attempts()
        return False
    return True

# Countdown timer
def lock_timer(code):
    remaining = 300 - (time.time() - attempt_data[code]["lock_time"])
    minutes = int(remaining) // 60
    seconds = int(remaining) % 60
    st.warning(f"🔒 Data locked! Try again in {minutes:02d}:{seconds:02d}")

# Streamlit UI
st.title("🛡️ Secure Data Encryption System")

# Navigation
menu = ["Home", "Store Data", "Retrieve Data", "Reauthorize", "View Records"]
choice = st.sidebar.selectbox("Navigation", menu)

# Home Tab
if choice == "Home":
    st.subheader("🏠 Welcome")
    st.write("This app lets you securely store and retrieve your encrypted data.")

# Store Data Tab
elif choice == "Store Data":
    st.subheader("📂 Store Data")
    user_data = st.text_area("Enter your data:")
    passkey = st.text_input("Enter passkey:", type="password")

    if st.button("Encrypt & Save"):
        if user_data and passkey:
            hashed = hash_passkey(passkey)
            encrypted = cipher.encrypt(user_data.encode()).decode()
            stored_data[encrypted] = {"data": encrypted, "passkey": hashed}
            save_data()
            st.success("✅ Data encrypted and saved!")
            st.code(encrypted, language="text")
        else:
            st.error("❗ Both fields are required.")

# Retrieve Data Tab
elif choice == "Retrieve Data":
    st.subheader("🔍 Retrieve Your Data")
    code = st.text_area("Enter your encryption code:")
    passkey = st.text_input("Enter your passkey:", type="password")

    if code:
        if is_locked(code):
            lock_timer(code)
        elif st.button("Decrypt"):
            if code in stored_data:
                hashed_input = hash_passkey(passkey)
                if stored_data[code]["passkey"] == hashed_input:
                    attempt_data[code] = {"attempts": 0, "lock_time": 0}
                    save_attempts()
                    decrypted = cipher.decrypt(code.encode()).decode()
                    st.success("✅ Data Decrypted!")
                    st.code(decrypted)
                else:
                    info = attempt_data.get(code, {"attempts": 0, "lock_time": 0})
                    info["attempts"] += 1
                    if info["attempts"] >= 3:
                        info["lock_time"] = time.time()
                        st.warning("🚫 Too many attempts! Data locked for 5 minutes.")
                    else:
                        st.error(f"❌ Incorrect passkey! Attempts left: {3 - info['attempts']}")
                    attempt_data[code] = info
                    save_attempts()
            else:
                st.error("❌ Code not found!")

# Reauthorization Tab
elif choice == "Reauthorize":
    st.subheader("🔑 Reauthorization")
    code = st.text_input("Enter your encryption code:")
    master_pass = st.text_input("Enter master password:", type="password")

    if st.button("Unlock"):
        if master_pass == "admin123":
            if code in attempt_data:
                attempt_data[code] = {"attempts": 0, "lock_time": 0}
                save_attempts()
                st.success("✅ Reauthorized! You can now try again.")
            else:
                st.error("❌ Code not found.")
        else:
            st.error("❌ Incorrect master password.")

# View Records Tab
elif choice == "View Records":
    st.subheader("📋 Stored Records")
    
    if stored_data:
        st.write("Here are your saved encryption codes:")
        for idx, code in enumerate(stored_data.keys(), start=1):
            st.code(code, language="text")
    else:
        st.info("📭 No data stored yet.")
