import streamlit as st
import numpy as np
import cv2
from pyzbar import pyzbar
from supabase import create_client, Client
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Kirana Cloud Manager", layout="wide")

# Connect to Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- NAVIGATION ---
menu = st.sidebar.radio("Main Menu", ["Dashboard", "Scan & Sell", "Add New Product", "Inventory List"])

# --- BARCODE DECODER FUNCTION ---
def decode_barcode(image_buffer):
    """Automatically finds and reads a barcode from an image buffer."""
    file_bytes = np.asarray(bytearray(image_buffer.read()), dtype=np.uint8)
    opencv_image = cv2.imdecode(file_bytes, 1)
    barcodes = pyzbar.decode(opencv_image)
    
    for barcode in barcodes:
        return barcode.data.decode("utf-8")
    return None

# --- PAGE: SCAN & SELL ---
if menu == "Scan & Sell":
    st.header("🔍 Quick Scan")
    cam_input = st.camera_input("Point at a product barcode")

    if cam_input:
        barcode_data = decode_barcode(cam_input)
        if barcode_data:
            st.success(f"Barcode Detected: {barcode_data}")
            # Search Supabase for this product
            res = supabase.table("products").select("*").eq("barcode", barcode_data).execute()
            if res.data:
                p = res.data[0]
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Product:** {p['name']}")
                    st.write(f"**Price:** ₹{p['selling_price']}")
                with col2:
                    new_qty = st.number_input("Update Stock", value=p['quantity'])
                    if st.button("Save Update"):
                        supabase.table("products").update({"quantity": new_qty}).eq("id", p['id']).execute()
                        st.balloons()
            else:
                st.warning("Product not found. Would you like to add it?")
                if st.button("Create New Product"):
                    st.session_state.new_barcode = barcode_data
                    # Redirect logic here
        else:
            st.error("Could not read barcode. Please try again with better lighting.")

# --- PAGE: INVENTORY LIST ---
elif menu == "Inventory List":
    st.header("📦 Current Stock")
    res = supabase.table("products").select("*").execute()
    if res.data:
        st.dataframe(res.data, use_container_width=True)
    else:
        st.info("No data found.")

# --- PAGE: ADD PRODUCT ---
elif menu == "Add New Product":
    st.header("➕ Add Item")
    with st.form("add_form"):
        name = st.text_input("Product Name")
        barcode = st.text_input("Barcode", value=st.session_state.get('new_barcode', ""))
        qty = st.number_input("Initial Quantity", min_value=0)
        sp = st.number_input("Selling Price", min_value=0.0)
        submitted = st.form_submit_button("Add to Cloud")
        
        if submitted:
            supabase.table("products").insert({"name": name, "barcode": barcode, "quantity": qty, "selling_price": sp}).execute()
            st.success("Product added successfully!")
