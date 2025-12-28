import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- APP CONFIG ---
st.set_page_config(page_title="Kirana Store Manager", layout="wide")
st.title("🛒 Kirana Inventory Online")

# --- DATABASE CONNECTION ---
# You will paste your Google Sheet URL in the sidebar of the running app
url = st.sidebar.text_input("Paste Google Sheet URL here:", type="password")

if url:
    conn = st.connection("gsheets", type=GSheetsConnection)

    # 1. Load Data with Auto-Initialization
    def load_data():
        try:
            data = conn.read(spreadsheet=url, ttl="0")
            if data.empty:
                # Create default headers if sheet is blank
                return pd.DataFrame(columns=["id", "name", "batch", "mfg_date", "exp_date", "barcode", "quantity", "purchase_price", "selling_price", "mrp"])
            return data
        except:
            return pd.DataFrame(columns=["id", "name", "batch", "mfg_date", "exp_date", "barcode", "quantity", "purchase_price", "selling_price", "mrp"])

    df = load_data()

    # 2. Navigation
    menu = ["View Stock", "Add Product", "Update Quantity", "Search"]
    choice = st.sidebar.selectbox("Menu", menu)

    # --- ADD PRODUCT ---
    if choice == "Add Product":
        st.subheader("Add New Item")
        with st.form("add_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Item Name")
                batch = st.text_input("Batch No")
                mfg = st.date_input("MFG Date")
                p_price = st.number_input("Purchase Price", min_value=0.0)
            with col2:
                barcode = st.text_input("Barcode")
                exp = st.date_input("Expiry Date")
                qty = st.number_input("Quantity", min_value=0, step=1)
                s_price = st.number_input("Selling Price", min_value=0.0)
            
            mrp = st.number_input("MRP", min_value=0.0)
            
            if st.form_submit_button("Save to Online Sheet"):
                new_data = pd.DataFrame([{
                    "id": len(df) + 1,
                    "name": name, "batch": batch, 
                    "mfg_date": mfg.strftime('%Y-%m-%d'), 
                    "exp_date": exp.strftime('%Y-%m-%d'),
                    "barcode": barcode, "quantity": qty,
                    "purchase_price": p_price, "selling_price": s_price, "mrp": mrp
                }])
                updated_df = pd.concat([df, new_data], ignore_index=True)
                conn.update(spreadsheet=url, data=updated_df)
                st.success(f"Saved {name} to your online records!")
                st.rerun()

    # --- VIEW STOCK ---
    elif choice == "View Stock":
        st.subheader("All Items in Store")
        st.dataframe(df, use_container_width=True, hide_index=True)

    # --- UPDATE QUANTITY ---
    elif choice == "Update Quantity":
        st.subheader("Update Stock Levels")
        item = st.selectbox("Select Product", df['name'].tolist())
        new_q = st.number_input("Enter New Total Quantity", min_value=0)
        if st.button("Update"):
            df.loc[df['name'] == item, 'quantity'] = new_q
            conn.update(spreadsheet=url, data=df)
            st.success("Stock Updated!")
            st.rerun()

    # --- SEARCH ---
    elif choice == "Search":
        search_term = st.text_input("Search by Name or Barcode")
        if search_term:
            results = df[df['name'].str.contains(search_term, case=False) | df['barcode'].astype(str).str.contains(search_term)]
            st.table(results)

else:
    st.warning("Please enter your Google Sheet URL in the sidebar to start.")
    st.info("How to get the URL: Create a blank Google Sheet -> Click Share -> Change to 'Anyone with link can Edit' -> Copy the link.")