import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
import pytz

# Page configuration
st.set_page_config(
    page_title="Smart Blind Stick Dashboard",
    page_icon="🦯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .alert-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 10px 0;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .sensor-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    h1 {
        color: #667eea;
        text-align: center;
        font-size: 2.5em;
        margin-bottom: 10px;
    }
    .datetime-display {
        text-align: center;
        color: #ffffff;
        font-size: 1.5em;
        margin-bottom: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Firebase - UPDATED FOR BOTH LOCAL AND CLOUD
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            # Try Streamlit Cloud secrets first
            firebase_config = dict(st.secrets["firebase_credentials"])
            firebase_admin.initialize_app(credentials.Certificate(firebase_config), {
                'databaseURL': st.secrets["FIREBASE_DATABASE_URL"]
            })
        except:
            # Fallback to local file for development
            firebase_admin.initialize_app(credentials.Certificate('firebase-key.json'), {
                'databaseURL': 'https://smartblindstick-42f49-default-rtdb.asia-southeast1.firebasedatabase.app'
            })
    return db.reference('/')

# Initialize session state for network history
if 'network_history' not in st.session_state:
    st.session_state.network_history = []

if 'latency_history' not in st.session_state:
    st.session_state.latency_history = []

# Get Firebase reference
ref = init_firebase()

# Dashboard Title
st.markdown("<h1>🦯 Smart Blind Stick Dashboard</h1>", unsafe_allow_html=True)

# Create placeholder for datetime that updates
datetime_placeholder = st.empty()

# Auto-refresh placeholder
placeholder = st.empty()
events_placeholder = st.empty()
stats_placeholder = st.empty()

# Malaysia timezone
malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')

while True:
    # Update datetime display with accurate Malaysia time
    current_datetime = datetime.now(malaysia_tz).strftime("%A, %B %d, %Y • %I:%M:%S %p")
    datetime_placeholder.markdown(f"<div class='datetime-display'>{current_datetime}</div>", unsafe_allow_html=True)
    
    # Fetch data from Firebase
    try:
        system_data = ref.child('system/status').get() or {}
        network_data = ref.child('network/latency').get() or {}
        emergency_events = ref.child('events/emergency').get() or {}
        obstacle_events = ref.child('events/obstacles').get() or {}
        rf_events = ref.child('events/rf').get() or {}
    except Exception as e:
        st.error(f"⚠️ Failed to connect to Firebase: {str(e)}")
        time.sleep(0.5)
        continue
    
    with placeholder.container():
        st.markdown("---")
        
        # ========== EMERGENCY ALERT SECTION ==========
        emergency_data = system_data.get('emergency', {})
        if emergency_data.get('active', False):
            st.markdown("""
            <div class="alert-card">
                <h2>🚨 EMERGENCY ALERT ACTIVE!</h2>
                <p style="font-size: 1.2em;">The emergency button has been pressed!</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ========== SENSORS & ACTUATORS ==========
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Ultrasonic Sensors")
            sensors = system_data.get('sensors', {})
            
            sensor1 = sensors.get('sensor1', {})
            sensor1_distance = sensor1.get('distance', 0)
            sensor1_detecting = sensor1.get('detecting', False)
            
            sensor1_html = f"""
            <div class="sensor-card">
                <h4>Sensor 1</h4>
                <p style="font-size: 1.3em; color: {'#ff0000' if sensor1_detecting else '#00ff00'};">
                    {sensor1_distance} cm {'⚠️ DETECTING' if sensor1_detecting else '✓ Clear'}
                </p>
            </div>
            """
            st.markdown(sensor1_html, unsafe_allow_html=True)
            
            sensor2 = sensors.get('sensor2', {})
            sensor2_distance = sensor2.get('distance', 0)
            sensor2_detecting = sensor2.get('detecting', False)
            
            sensor2_html = f"""
            <div class="sensor-card">
                <h4>Sensor 2</h4>
                <p style="font-size: 1.3em; color: {'#ff0000' if sensor2_detecting else '#00ff00'};">
                    {sensor2_distance} cm {'⚠️ DETECTING' if sensor2_detecting else '✓ Clear'}
                </p>
            </div>
            """
            st.markdown(sensor2_html, unsafe_allow_html=True)
        
        with col2:
            st.subheader("🔊 Actuators Status")
            actuators = system_data.get('actuators', {})
            rf_active = system_data.get('rf', {}).get('active', False)
            
            buzzer_active = actuators.get('buzzer', False)
            vibration_active = actuators.get('vibration', False)
            
            rf_html = f"""
            <div class="sensor-card">
                <h4>RF Receiver</h4>
                <p style="font-size: 1.3em; color: {'#00ff00' if rf_active else '#888888'};">
                    {'📡 SIGNAL DETECTED' if rf_active else '📡 No Signal'}
                </p>
            </div>
            """
            st.markdown(rf_html, unsafe_allow_html=True)
            
            buzzer_html = f"""
            <div class="sensor-card">
                <h4>Buzzer</h4>
                <p style="font-size: 1.3em; color: {'#00ff00' if buzzer_active else '#888888'};">
                    {'🔊 ACTIVE' if buzzer_active else '🔇 Inactive'}
                </p>
            </div>
            """
            st.markdown(buzzer_html, unsafe_allow_html=True)
            
            vibration_html = f"""
            <div class="sensor-card">
                <h4>Vibration Motor</h4>
                <p style="font-size: 1.3em; color: {'#00ff00' if vibration_active else '#888888'};">
                    {'📳 ACTIVE' if vibration_active else '📴 Inactive'}
                </p>
            </div>
            """
            st.markdown(vibration_html, unsafe_allow_html=True)

        st.markdown("---")
        
        # ========== EMERGENCY BUTTON STATUS (FIXED) ==========
        st.subheader("🚨 Emergency Button Status")
        emergency_active = emergency_data.get('active', False)
        
        emergency_btn_html = f"""
        <div class="sensor-card" style="border-left: 4px solid {'#ff0000' if emergency_active else '#888888'};">
            <h4>Emergency Button</h4>
            <p style="font-size: 1.5em; color: {'#ff0000' if emergency_active else '#00ff00'}; font-weight: bold;">
                {'🚨 EMERGENCY ACTIVATED!' if emergency_active else '🟢 Standby Mode'}
            </p>
        </div>
        """
        st.markdown(emergency_btn_html, unsafe_allow_html=True)

        st.markdown("---")

        # ========== NETWORK PERFORMANCE TABLE (NO GRAPH) ==========
        st.subheader("📊 Network Performance")
        
        latency = network_data.get('current', 0)
        # Use accurate Malaysia time for timestamp
        timestamp = datetime.now(malaysia_tz).strftime("%H:%M:%S")
        status = network_data.get('status', 'unknown')
        rssi = system_data.get('wifi', {}).get('rssi', 0)
        
        emergency_active = emergency_data.get('active', False)
        
        event_type = "System Idle"
        if emergency_active:
            event_type = "GPS Location Update"
        elif sensor1_detecting or sensor2_detecting:
            event_type = f"Sensor {'1' if sensor1_detecting else '2'} Reading"
        elif rf_active:
            event_type = "RF Signal Received"
        else:
            event_type = "System Monitoring"
        
        new_entry = {
            'No': len(st.session_state.network_history) + 1,
            'Timestamp': timestamp,
            'Event Type': event_type,
            'Latency (ms)': latency,
            'RTT (ms)': latency * 2,
            'Signal Strength (dBm)': rssi,
            'Packet Size (bytes)': 512,
            'Transmission Result': status.upper(),
            'Network Status': 'Connected' if status == 'success' else 'Failed'
        }
        
        if len(st.session_state.network_history) == 0 or st.session_state.network_history[-1]['Timestamp'] != timestamp:
            st.session_state.network_history.append(new_entry)
            
            if len(st.session_state.network_history) > 20:
                st.session_state.network_history.pop(0)
                for i, entry in enumerate(st.session_state.network_history):
                    entry['No'] = i + 1
        
        df_network = pd.DataFrame(st.session_state.network_history)
        st.dataframe(df_network, use_container_width=True, height=400)

    with events_placeholder.container():
        st.markdown("---")
        st.subheader("📋 Event History")
        
        tab1, tab2, tab3 = st.tabs(["🚨 Emergency", "⚠️ Obstacles", "📡 RF Events"])
        
        with tab1:
            if emergency_events:
                emergency_list = []
                counter = 1
                
                for key, event in emergency_events.items():
                    lat = event.get('latitude', '0')
                    lon = event.get('longitude', '0')
                    city = event.get('city', 'Unknown')
                    
                    emergency_list.append({
                        'No': counter,
                        'Time': event.get('timestamp', 'N/A'),
                        'Location': f"{lat}, {lon}",
                        'City': city,
                        'Status': event.get('status', 'N/A').upper(),
                        'Notification': '✓ Sent' if event.get('notificationSent', False) else '✗ Failed'
                    })
                    counter += 1
                    
                df_emergency = pd.DataFrame(emergency_list)
                st.dataframe(df_emergency, use_container_width=True, height=300)
                
                if emergency_list:
                    latest = emergency_list[-1]
                    coords = latest['Location'].split(', ')
                    if len(coords) == 2:
                        try:
                            lat, lon = float(coords[0]), float(coords[1])
                            if lat != 0 and lon != 0:
                                st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=13)
                            else:
                                st.warning("⚠️ GPS location not available. Waiting for location data...")
                        except:
                            st.warning("⚠️ Invalid GPS coordinates")
            else:
                st.info("No emergency events recorded")
        
        with tab2:
            if obstacle_events:
                obstacle_list = []
                counter = 1
                for key, event in obstacle_events.items():
                    obstacle_list.append({
                        'No': counter,
                        'Time': event.get('timestamp', 'N/A'),
                        'Sensor 1 (cm)': event.get('sensor1', 0),
                        'Sensor 2 (cm)': event.get('sensor2', 0)
                    })
                    counter += 1
                df_obstacles = pd.DataFrame(obstacle_list)
                st.dataframe(df_obstacles, use_container_width=True, height=300)
            else:
                st.info("No obstacle events recorded")
        
        with tab3:
            if rf_events:
                rf_list = []
                counter = 1
                for key, event in rf_events.items():
                    rf_list.append({
                        'No': counter,
                        'Time': event.get('timestamp', 'N/A'),
                        'Status': event.get('status', 'N/A').upper()
                    })
                    counter += 1
                df_rf = pd.DataFrame(rf_list)
                st.dataframe(df_rf, use_container_width=True, height=300)
            else:
                st.info("No RF events recorded")

    with stats_placeholder.container():
        st.markdown("---")
        st.subheader("📈 Statistics Summary")
        
        total_emergencies = len(emergency_events) if emergency_events else 0
        total_obstacles = len(obstacle_events) if obstacle_events else 0
        total_rf = len(rf_events) if rf_events else 0
        
        col1, col2, col3 = st.columns(3)
        
        col1.metric("🚨 Emergency Alerts Triggered", total_emergencies)
        col2.metric("⚠️ Obstacles Detected", total_obstacles)
        col3.metric("📡 RF Events Captured", total_rf)

    time.sleep(0.2)
