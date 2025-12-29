import streamlit as st
from supabase import create_client, Client
import cv2
import numpy as np
from pyzbar import pyzbar
import pandas as pd
from datetime import datetime

# --- 1. AUTHENTICATION (SECURE LOGIN) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔐 Shop Login")
        pwd = st.text_input("Enter Admin Password", type="password")
        if st.button("Login"):
            if pwd == st.secrets["APP_PASSWORD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Invalid Password")
        return False
    return True

if not check_password():
    st.stop()

# --- 2. DATABASE & CONFIG ---
st.set_page_config(page_title="Kirana ERP Cloud", layout="wide")
supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- 3. SESSION STATE FOR BILLING ---
if 'cart' not in st.session_state:
    st.session_state.cart = []

# --- 4. THE INTERFACE ---
tabs = st.tabs(["🛒 POS & Billing", "📦 Inventory Master", "📊 Reports"])

# --- TAB 1: POS & BILLING ---
with tabs[0]:
    col_scan, col_bill = st.columns([1, 1])
    
    with col_scan:
        st.subheader("Scan Items")
        img = st.camera_input("Scan Barcode")
        
        if img:
            # Automatic Decoding
            file_bytes = np.asarray(bytearray(img.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, 1)
            decoded = pyzbar.decode(frame)
            
            if decoded:
                barcode = decoded[0].data.decode("utf-8")
                res = supabase.table("products").select("*").eq("barcode", barcode).execute()
                if res.data:
                    item = res.data[0]
                    st.session_state.cart.append(item)
                    st.success(f"Added: {item['name']}")
                else:
                    st.error("Product not found!")

    with col_bill:
        st.subheader("Current Bill")
        if st.session_state.cart:
            df_cart = pd.DataFrame(st.session_state.cart)
            st.table(df_cart[['name', 'selling_price']])
            total = df_cart['selling_price'].sum()
            st.write(f"### Total: ₹{total}")
            
            if st.button("Generate & Print Bill"):
                # Logic for Printing
                st.write("---")
                st.markdown(f"""
                <div id="thermal-bill" style="width: 80mm; font-family: 'Courier New', Courier, monospace; font-size: 12px; border: 1px solid #ccc; padding: 10px;">
                    <center><strong>MY KIRANA STORE</strong></center>
                    <center>Patna, Bihar</center>
                    <hr>
                    {"".join([f"<p>{i['name']} <span style='float:right;'>₹{i['selling_price']}</span></p>" for i in st.session_state.cart])}
                    <hr>
                    <p><strong>TOTAL <span style='float:right;'>₹{total}</span></strong></p>
                    <center>Thank You! Visit Again</center>
                </div>
                """, unsafe_allow_index=True)
                
                # Trigger Browser Print for Thermal Printer
                st.button("Click to Print to Thermal Printer", on_click=lambda: st.write('<script>window.print();</script>', unsafe_allow_html=True))
                
                # Clear cart after billing
                if st.button("Clear Bill"):
                    st.session_state.cart = []
                    st.rerun()
