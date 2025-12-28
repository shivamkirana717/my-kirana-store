import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. Login Logic ---
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔐 Kirana Store Login")
        pwd = st.text_input("Enter Password", type="password")
        if st.button("Login"):
            # This checks the password we saved in "Secrets"
            if pwd == st.secrets["passwords"]["store_pass"]:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Incorrect Password")
        st.stop() # Stops the app here until login is successful

# --- 2. Start Protected App ---
check_login()

st.title("🛒 Kirana Inventory Online")
try:
    # This automatically finds the URL from your Secrets
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0")
except:
    st.error("Connection failed. Check your Secrets for the correct Sheet URL.")
    st.stop()

# --- 3. App Menu ---
menu = ["View Stock", "Add Product", "Update Quantity"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Add Product":
    st.subheader("Add New Item")
    with st.form("add_item"):
        name = st.text_input("Item Name")
        qty = st.number_input("Initial Quantity", min_value=0)
        if st.form_submit_button("Save to Cloud"):
            new_row = pd.DataFrame([{"id": len(df)+1, "name": name, "quantity": qty}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df) # This works now because of Secrets
            st.success(f"Added {name}!")
            st.rerun()

elif choice == "View Stock":
    st.dataframe(df, use_container_width=True)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()
