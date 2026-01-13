import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# Initialize Firebase
if not firebase_admin._apps:
    # Try to load from Streamlit secrets (for cloud deployment)
    try:
        firebase_config = dict(st.secrets["firebase_credentials"])
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {
            'databaseURL': st.secrets["FIREBASE_DATABASE_URL"]
        })
    except:
        # Fallback to local file (for local development)
        cred = credentials.Certificate('firebase-key.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://smartblindstick-42f49-default-rtdb.asia-southeast1.firebasedatabase.app"
        })

# Page config
st.set_page_config(
    page_title="Smart Blind Stick Dashboard",
    page_icon="🦯",
    layout="wide"
)

# Title
st.title("🦯 Smart Blind Stick Dashboard")
st.markdown("---")

# Sidebar
st.sidebar.header("⚙️ Settings")
device_ref = db.reference('devices')
devices = device_ref.get() or {}

if not devices:
    st.sidebar.warning("Tiada device dijumpai")
    selected_device = None
else:
    device_list = list(devices.keys())
    selected_device = st.sidebar.selectbox("Pilih Device:", device_list)

refresh_rate = st.sidebar.slider("Refresh Rate (saat):", 1, 10, 5)

# Auto refresh
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# Main content
if selected_device:
    device_data = devices[selected_device]
    
    # Latest readings
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📏 Jarak (cm)",
            f"{device_data.get('distance', 'N/A')}",
            help="Jarak halangan di hadapan"
        )
    
    with col2:
        st.metric(
            "🔊 Bunyi",
            "ON" if device_data.get('buzzer', False) else "OFF",
            help="Status buzzer"
        )
    
    with col3:
        st.metric(
            "⚡ Bateri (%)",
            f"{device_data.get('battery', 'N/A')}",
            help="Tahap bateri device"
        )
    
    with col4:
        gps = device_data.get('gps', {})
        st.metric(
            "📍 Lokasi",
            "Aktif" if gps else "Tidak aktif",
            help="Status GPS"
        )
    
    st.markdown("---")
    
    # GPS Map
    if gps and 'lat' in gps and 'lon' in gps:
        st.subheader("🗺️ Lokasi GPS")
        df_map = pd.DataFrame({
            'lat': [gps['lat']],
            'lon': [gps['lon']]
        })
        st.map(df_map, zoom=15)
    
    # Historical data
    st.subheader("📊 Data Sejarah")
    history_ref = db.reference(f'history/{selected_device}')
    history = history_ref.get() or {}
    
    if history:
        df = pd.DataFrame(history.values())
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Distance chart
        fig = px.line(df, x='timestamp', y='distance', 
                     title='Graf Jarak vs Masa',
                     labels={'distance': 'Jarak (cm)', 'timestamp': 'Masa'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Battery chart
        fig2 = px.line(df, x='timestamp', y='battery',
                      title='Graf Bateri vs Masa',
                      labels={'battery': 'Bateri (%)', 'timestamp': 'Masa'})
        st.plotly_chart(fig2, use_container_width=True)
        
        # Data table
        st.subheader("📋 Jadual Data")
        st.dataframe(df.sort_values('timestamp', ascending=False), use_container_width=True)
    else:
        st.info("Tiada data sejarah lagi")

else:
    st.info("Sila pilih device dari sidebar")

# Footer
st.markdown("---")
st.caption("Smart Blind Stick Dashboard © 2024")
