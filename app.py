import streamlit as st
from supabase import create_client, Client

# --- SETUP ---
st.set_page_config(page_title="Shop Manager Web", layout="wide")

# Connect to Supabase using Streamlit Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📦 Live Shop Inventory")

# --- MOBILE BARCODE SCANNER ---
st.subheader("Scan Barcode")
# This uses the phone's native camera to take a photo of a barcode
img_file = st.camera_input("Scan a barcode to search")

if img_file:
    # In a full implementation, you'd use a library like 'pyzbar' here to decode.
    # For now, this prepares the interface for search.
    st.info("Barcode image captured. Searching database...")

# --- SEARCH ---
search_query = st.text_input("Search by Name or Barcode")

# --- DATA DISPLAY ---
def fetch_data():
    if search_query:
        # Search filter
        res = supabase.table("products").select("*").ilike("name", f"%{search_query}%").execute()
    else:
        # Show all
        res = supabase.table("products").select("*").order("id").execute()
    return res.data

data = fetch_data()

if data:
    # Display as a clean table
    st.dataframe(data, use_container_width=True)
    
    # Quick Stats
    total_qty = sum(item['quantity'] for item in data)
    st.metric("Total Items in Stock", total_qty)
else:
    st.warning("No products found in the cloud.")

# --- ADD QUICK QUANTITY UPDATE ---
with st.expander("Update Quantity via Web"):
    with st.form("update_form"):
        prod_id = st.number_input("Product ID", step=1)
        new_qty = st.number_input("New Quantity", step=1)
        submit = st.form_submit_button("Update Inventory")
        
        if submit:
            supabase.table("products").update({"quantity": new_qty}).eq("id", prod_id).execute()
            st.success(f"ID {prod_id} updated! Refresh to see changes.")
            st.rerun()
