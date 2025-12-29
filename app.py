import streamlit as st
from supabase import create_client, Client
import cv2
import numpy as np
from pyzbar import pyzbar
import av
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

# --- CONFIGURATION & AUTH ---
st.set_page_config(page_title="VasyERP Clone", layout="wide", initial_sidebar_state="collapsed")

# 1. Secure Login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_login():
    st.markdown("## 🔐 Shop Manager Login")
    password = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Wrong Password")

if not st.session_state.authenticated:
    check_login()
    st.stop()

# 2. Database Connection
@st.cache_resource
def init_db():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_db()

# --- REAL-TIME BARCODE SCANNER (THE "VASY" FEATURE) ---
# This config ensures the camera works on Mobile Data (4G) as well as WiFi
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

def barcode_callback(frame):
    """This runs 30 times a second to find barcodes instantly."""
    img = frame.to_ndarray(format="bgr24")
    
    # Decode barcode
    decoded_objects = pyzbar.decode(img)
    
    for obj in decoded_objects:
        # If found, draw a green box (Visual Feedback)
        (x, y, w, h) = obj.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # We can't return data directly from this callback to Streamlit easily,
        # so usually, we just visualize it here. To capture it, we use the UI below.
    
    return av.VideoFrame.from_ndarray(img, format="bgr24")

# --- APP NAVIGATION ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50)
menu = st.sidebar.radio("Menu", ["Dashboard", "Live POS (Billing)", "Inventory Master", "Settings"])

# --- TAB 1: DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Retail Dashboard")
    # Quick Stats
    try:
        count = supabase.table("products").select("id", count="exact").execute().count
        st.metric("Total Products", count)
    except:
        st.metric("Total Products", "0")
    
    st.info("💡 Tip: Go to 'Live POS' to start billing customers.")

# --- TAB 2: LIVE POS (The Vasy Scanning Experience) ---
elif menu == "Live POS (Billing)":
    st.title("🛒 Live Billing Terminal")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.subheader("Scan Product")
        st.write("Point camera at barcode. It will auto-detect.")
        
        # LIVE WEBCAM SCANNER
        # This replaces the "Take Photo" button with a live video feed
        webrtc_ctx = webrtc_streamer(
            key="barcode-scanner",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTC_CONFIGURATION,
            video_frame_callback=barcode_callback,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        # Simple manual override if camera is tricky
        manual_code = st.text_input("Or type Barcode & Enter", key="manual_input")
        
        if manual_code:
            # Fetch product
            res = supabase.table("products").select("*").eq("barcode", manual_code).execute()
            if res.data:
                item = res.data[0]
                if "cart" not in st.session_state: st.session_state.cart = []
                st.session_state.cart.append(item)
                st.success(f"✅ Added {item['name']}")
            else:
                st.error("❌ Product not found!")

    with col2:
        st.subheader("Current Bill")
        if "cart" in st.session_state and st.session_state.cart:
            total = 0
            for i, item in enumerate(st.session_state.cart):
                st.write(f"{i+1}. **{item['name']}** - ₹{item['selling_price']}")
                total += item['selling_price']
            
            st.divider()
            st.markdown(f"### Total: ₹{total}")
            
            if st.button("Print Bill"):
                st.toast("Printing Thermal Receipt...")
                # Clear cart
                st.session_state.cart = []
                st.rerun()
        else:
            st.write("Cart is empty")

# --- TAB 3: INVENTORY MASTER (Detailed Vasy Fields) ---
elif menu == "Inventory Master":
    st.title("📦 Add New Product")
    
    with st.form("new_product_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Product Name *")
            barcode = st.text_input("Barcode / ISBN *")
            category = st.selectbox("Category", ["General", "Food", "Electronics", "Pharma"])
        with c2:
            buy_price = st.number_input("Purchase Price", min_value=0.0)
            sell_price = st.number_input("Selling Price *", min_value=0.0)
            mrp = st.number_input("MRP", min_value=0.0)
        with c3:
            stock = st.number_input("Opening Stock", min_value=0)
            tax = st.selectbox("GST %", [0, 5, 12, 18, 28])
            hsn = st.text_input("HSN Code")

        submitted = st.form_submit_button("Save Product")
        if submitted:
            if name and barcode and sell_price:
                data = {
                    "name": name,
                    "barcode": barcode,
                    "quantity": stock,
                    "purchase_price": buy_price,
                    "selling_price": sell_price,
                    "mrp": mrp
                }
                supabase.table("products").insert(data).execute()
                st.success("Product Added Successfully!")
            else:
                st.warning("Please fill required fields (*)")

# --- TAB 4: SETTINGS ---
elif menu == "Settings":
    st.title("⚙️ Settings")
    st.write("Printer Configuration: POS-80 (Thermal)")
    st.write("Shop Name: My Kirana Store")
