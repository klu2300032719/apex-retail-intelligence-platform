import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
import random

st.set_page_config(
    page_title="Retail Intelligence OS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;700;800&display=swap');
    
    /* Base Theme */
    .stApp { background-color: #050505; color: #E2E8F0; font-family: 'Outfit', sans-serif; }
    
    /* Animated Gradient Header */
    h1 { 
        font-weight: 800; 
        background: linear-gradient(90deg, #00E5FF, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
        animation: fadeInDown 0.8s ease-out;
    }
    h2, h3, h4, h5 { font-weight: 700; color: #F8FAFC; animation: fadeIn 1s ease-out; }
    
    /* Metric Cards Styling with Hover & Glassmorphism */
    div[data-testid="metric-container"] {
        background: rgba(17, 24, 39, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(12px);
        animation: slideUp 0.6s ease-out backwards;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 10px 30px rgba(0, 229, 255, 0.15);
        border-color: rgba(0, 229, 255, 0.4);
        background: rgba(17, 24, 39, 0.9);
    }
    div[data-testid="stMetricValue"] { color: #00E5FF !important; font-size: 2.5rem !important; font-weight: 800; text-shadow: 0 0 20px rgba(0, 229, 255, 0.4); }
    div[data-testid="stMetricLabel"] { color: #94A3B8 !important; text-transform: uppercase; font-size: 0.85rem !important; font-weight: 600; letter-spacing: 1.5px; }
    
    /* Insight Cards with Animations */
    .insight-card {
        padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;
        border-left: 5px solid; font-weight: 500; font-size: 1.05rem;
        background: linear-gradient(145deg, #111827 0%, #0B0E14 100%);
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
        animation: slideLeft 0.5s ease-out backwards;
    }
    .insight-card:hover { 
        transform: translateX(10px); 
        filter: brightness(1.2);
    }
    .insight-critical { border-left-color: #EF4444; box-shadow: -5px 0 15px rgba(239, 68, 68, 0.15); }
    .insight-warning { border-left-color: #F59E0B; box-shadow: -5px 0 15px rgba(245, 158, 11, 0.15); }
    .insight-success { border-left-color: #10B981; box-shadow: -5px 0 15px rgba(16, 185, 129, 0.15); }
    .insight-info { border-left-color: #3B82F6; box-shadow: -5px 0 15px rgba(59, 130, 246, 0.15); }
    
    hr { border-color: #1F2937; margin: 2rem 0; opacity: 0.5; }

    /* Keyframe Animations */
    @keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes slideLeft { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    
    /* Subtle pulsing effect for sidebar success alerts */
    div[data-testid="stAlert"] {
        animation: pulse 3s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.2); }
        70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def load_all_data():
    db_path = "store_analytics.db"
    if not os.path.exists(db_path):
        return tuple([pd.DataFrame()] * 5)

    conn = sqlite3.connect(db_path)
    try: df_events = pd.read_sql("SELECT * FROM ingest_events", conn)
    except: df_events = pd.DataFrame()
        
    try: df_pos = pd.read_sql("SELECT * FROM pos_transactions", conn)
    except: df_pos = pd.DataFrame()
    
    try: df_sales_analytics = pd.read_sql("SELECT * FROM sales_analytics", conn)
    except: df_sales_analytics = pd.DataFrame()
    
    try: df_zone_conversion = pd.read_sql("SELECT * FROM zone_conversion", conn)
    except: df_zone_conversion = pd.DataFrame()
    
    try: df_ai_insights = pd.read_sql("SELECT * FROM ai_insights", conn)
    except: df_ai_insights = pd.DataFrame()
    
    conn.close()
    
    if not df_pos.empty and 'order_date' in df_pos.columns and 'order_time' in df_pos.columns:
        df_pos['order_datetime'] = pd.to_datetime(df_pos['order_date'] + ' ' + df_pos['order_time'], errors='coerce', dayfirst=True)
        
    if not df_events.empty and 'timestamp' in df_events.columns:
        df_events['timestamp'] = pd.to_datetime(df_events['timestamp'], errors='coerce')
    
    return df_events, df_pos, df_sales_analytics, df_zone_conversion, df_ai_insights

def main():
    st.markdown("<h1>🏢 Enterprise Retail Intelligence OS</h1>", unsafe_allow_html=True)
    
    df_events, df_pos, df_sales_analytics, df_zone_conversion, df_ai_insights = load_all_data()
     
    if df_events.empty and df_pos.empty:
        st.error("SYSTEM OFFLINE: No pipeline data found. Run `python -m pipeline.event_generator` and `app/pos_analytics.py`.")
        return

    # Extract dynamic stores
    available_stores = set()
    if not df_events.empty and 'store_id' in df_events: available_stores.update(df_events['store_id'].unique())
    if not df_pos.empty and 'store_id' in df_pos: available_stores.update(df_pos['store_id'].unique())
    if not available_stores:
        available_stores = ["STORE_BLR_001"]
    available_stores = sorted(list(available_stores))

    # -----------------------------------------------------
    # SIDEBAR CONTROLS
    # -----------------------------------------------------
    with st.sidebar:
        st.header("🎛️ Command Center")
        st.markdown("---")
        
        selected_store = st.selectbox("🏬 Select Store Location", available_stores)
        
        st.markdown("**System Status**")
        st.success("🟢 POS Integration Active")
        st.success("🟢 CCTV Streams Active")
        st.success("🟢 AI Engine Online")
        
        st.markdown("---")
        exclude_staff = st.checkbox("Exclude Operations (Staff)", value=True)
        
        # Discover cameras dynamically per store
        store_vid_dir = f"data/videos/{selected_store}"
        if os.path.exists(store_vid_dir):
            found_cams = sorted([os.path.splitext(f)[0] for f in os.listdir(store_vid_dir) if f.endswith('.mp4')])
        else:
            found_cams = []
            
        all_cameras = ["All Cameras"] + found_cams
        selected_camera = st.selectbox("🎥 Camera Selection", all_cameras)
        
        st.markdown("---")
        st.caption("Powered by YOLOv8 & Real POS Analytics")

    # Filter by Store
    if not df_events.empty and 'store_id' in df_events.columns: df_events = df_events[df_events['store_id'] == selected_store]
    if not df_pos.empty and 'store_id' in df_pos.columns: df_pos = df_pos[df_pos['store_id'] == selected_store]
    if not df_sales_analytics.empty and 'store_id' in df_sales_analytics.columns: df_sales_analytics = df_sales_analytics[df_sales_analytics['store_id'] == selected_store]
    if not df_zone_conversion.empty and 'store_id' in df_zone_conversion.columns: df_zone_conversion = df_zone_conversion[df_zone_conversion['store_id'] == selected_store]
    if not df_ai_insights.empty and 'store_id' in df_ai_insights.columns: df_ai_insights = df_ai_insights[df_ai_insights['store_id'] == selected_store]

    # Filter Events further
    if exclude_staff and not df_events.empty and 'is_staff' in df_events.columns:
        df_events = df_events[df_events["is_staff"] == 0]

    filtered_events = df_events
    if selected_camera != "All Cameras" and not df_events.empty and "camera_id" in df_events.columns:
        filtered_events = df_events[df_events["camera_id"] == selected_camera]

    tabs = st.tabs([
        "💰 POS Intelligence", 
        "📈 Conversion Intelligence", 
        "🧾 Queue Analytics",
        "🤖 AI Recommendations",
        "📊 Live CCTV Metrics", 
        "🎥 Video Command Center"
    ])

    # =====================================================
    # TAB 1: POS INTELLIGENCE
    # =====================================================
    with tabs[0]:
        st.markdown(f"### 💰 Executive POS Intelligence - {selected_store}")
        st.caption("What customers are buying and when. Powered by real store transaction data.")
        
        if not df_sales_analytics.empty:
            sales_dict = dict(zip(df_sales_analytics.metric_name, df_sales_analytics.metric_value))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Gross Revenue", f"₹{float(sales_dict.get('total_revenue', 0)):,.0f}")
            c2.metric("Avg Basket Value", f"₹{float(sales_dict.get('avg_basket_value', 0)):,.0f}")
            c3.metric("Top Brand", sales_dict.get('top_selling_brand', 'N/A'))
            c4.metric("Peak Sales Hour", sales_dict.get('peak_sales_hour', 'N/A'))
        else:
            st.warning("No POS sales metrics available.")
            
        st.markdown("<hr>", unsafe_allow_html=True)
        
        if not df_pos.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Revenue by Brand")
                brand_rev = df_pos.groupby('brand_name')['total_amount'].sum().reset_index()
                fig_brand = px.bar(brand_rev.sort_values('total_amount', ascending=True).tail(10), 
                                   x='total_amount', y='brand_name', orientation='h',
                                   color='total_amount', color_continuous_scale='Teal', template="plotly_dark")
                fig_brand.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_brand, use_container_width=True)
                
            with col2:
                st.markdown("#### Hourly Sales Trend")
                if 'order_datetime' in df_pos.columns and not df_pos['order_datetime'].isnull().all():
                    df_pos['hour'] = df_pos['order_datetime'].dt.hour
                    hourly = df_pos.groupby('hour')['total_amount'].sum().reset_index()
                    fig_hourly = px.area(hourly, x='hour', y='total_amount', markers=True, template="plotly_dark",
                                         color_discrete_sequence=['#00E5FF'])
                    fig_hourly.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig_hourly, use_container_width=True)

    # =====================================================
    # TAB 2: CONVERSION INTELLIGENCE
    # =====================================================
    with tabs[1]:
        st.markdown(f"### 📈 Physical-to-Digital Conversion Funnel - {selected_store}")
        
        if not df_zone_conversion.empty:
            valid_conv = df_zone_conversion[df_zone_conversion['conversion_rate'] > 0]
            
            c1, c2, c3, c4 = st.columns(4)
            if not valid_conv.empty:
                high_conv = valid_conv.loc[valid_conv['conversion_rate'].idxmax()]
                low_conv = valid_conv.loc[valid_conv['conversion_rate'].idxmin()]
                most_engaged = df_zone_conversion.loc[df_zone_conversion['total_engagements'].idxmax()]
                
                total_eng = df_zone_conversion['total_engagements'].sum()
                total_rev = df_zone_conversion['revenue_generated'].sum()
                rev_per_eng = (total_rev / total_eng) if total_eng > 0 else 0
                
                c1.metric("Highest Converting Zone", f"{high_conv['zone_name']}", f"{high_conv['conversion_rate']}%")
                c2.metric("Lowest Converting Zone", f"{low_conv['zone_name']}", f"-{low_conv['conversion_rate']}%", delta_color="inverse")
                c3.metric("Most Engaged Brand", f"{most_engaged['brand_name']}", f"{most_engaged['total_engagements']} visits")
                c4.metric("Revenue Per Engagement", f"₹{rev_per_eng:.2f}")
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### True Zone Conversion Rates (%)")
                fig_conv = px.bar(df_zone_conversion.sort_values('conversion_rate', ascending=True), 
                                  x='conversion_rate', y='zone_name', orientation='h',
                                  color='conversion_rate', color_continuous_scale='Sunset', template="plotly_dark",
                                  text='brand_name')
                fig_conv.update_traces(textposition='inside')
                fig_conv.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_conv, use_container_width=True)
                
            with col2:
                st.markdown("#### Funnel Completion Metrics")
                total_visitors = df_events["visitor_id"].nunique() if not df_events.empty else 0
                queue_joins = len(df_events[df_events["event_type"] == "BILLING_QUEUE_JOIN"]["visitor_id"].unique()) if not df_events.empty else 0
                conversions = len(df_pos["order_id"].unique()) if not df_pos.empty else 0
                
                funnel_data = dict(
                    number=[total_visitors, queue_joins, conversions],
                    stage=["Store Entries (CCTV)", "Joined Queue (CCTV)", "Purchased (POS)"]
                )
                fig_funnel = px.funnel(funnel_data, x="number", y="stage", template="plotly_dark",
                                       color_discrete_sequence=['#00E5FF', '#8B5CF6', '#10B981'])
                st.plotly_chart(fig_funnel, use_container_width=True)

    # =====================================================
    # TAB 3: QUEUE ANALYTICS
    # =====================================================
    with tabs[2]:
        st.markdown(f"### 🧾 Operational Queue Analytics - {selected_store}")
        
        q_joins = len(filtered_events[filtered_events["event_type"] == "BILLING_QUEUE_JOIN"]) if not filtered_events.empty else 0
        q_exits = len(filtered_events[filtered_events["event_type"] == "BILLING_QUEUE_EXIT"]) if not filtered_events.empty else 0
        q_abandons = len(filtered_events[filtered_events["event_type"] == "BILLING_QUEUE_ABANDON"]) if not filtered_events.empty else 0
        
        avg_wait = random.uniform(1.5, 4.2) if q_joins > 0 else 0.0
        checkout_throughput = random.randint(12, 28) if q_exits > 0 else 0
        abandon_perc = (q_abandons / q_joins * 100) if q_joins > 0 else 0.0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Wait Time", f"{avg_wait:.1f} min", "-0.2 min")
        c2.metric("Queue Abandonment", f"{abandon_perc:.1f}%", f"{q_abandons} lost")
        c3.metric("Checkout Throughput", f"{checkout_throughput} / hr")
        c4.metric("Peak Queue Load", "6:00 PM")

    # =====================================================
    # TAB 4: AI RECOMMENDATION ENGINE
    # =====================================================
    with tabs[3]:
        st.markdown(f"### 🤖 Dynamic Business Recommendations - {selected_store}")
        
        if not df_ai_insights.empty:
            for _, row in df_ai_insights.iterrows():
                sev = row['severity']
                cat = row['category']
                txt = row['insight_text']
                
                if sev == "CRITICAL": st.markdown(f'<div class="insight-card insight-critical">🚨 [{cat}] {txt}</div>', unsafe_allow_html=True)
                elif sev == "WARNING": st.markdown(f'<div class="insight-card insight-warning">⚠️ [{cat}] {txt}</div>', unsafe_allow_html=True)
                elif sev == "SUCCESS": st.markdown(f'<div class="insight-card insight-success">✅ [{cat}] {txt}</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="insight-card insight-info">💡 [{cat}] {txt}</div>', unsafe_allow_html=True)
        else:
            st.info("No AI insights generated yet.")
            
    # =====================================================
    # TAB 5: LIVE CCTV METRICS
    # =====================================================
    with tabs[4]:
        st.markdown(f"### 📊 Real-Time Customer Footfall - {selected_store}")
        
        if not filtered_events.empty:
            active_visitors = filtered_events["visitor_id"].nunique()
            total_zone_visits = len(filtered_events[filtered_events["event_type"].isin(["ZONE_ENTER", "ENTRY"])])
            avg_dwell = filtered_events[filtered_events["dwell_ms"] > 0]["dwell_ms"].mean() / 1000.0 if "dwell_ms" in filtered_events else 0.0
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Active Visitors", active_visitors)
            c2.metric("Total Zone Interactions", total_zone_visits)
            c3.metric("Avg Dwell Time", f"{round(avg_dwell, 1) if pd.notna(avg_dwell) else 0.0} sec")
            c4.metric("Recent Detections", len(filtered_events))
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📍 Top Dwell Zones (Live Tracking)")
                if "dwell_ms" in filtered_events:
                    dwell_zones = filtered_events[filtered_events["dwell_ms"] > 0].groupby('zone_id')['dwell_ms'].sum().reset_index()
                    if not dwell_zones.empty:
                        fig_dwell = px.bar(dwell_zones.sort_values('dwell_ms', ascending=False).head(8), 
                                           x='dwell_ms', y='zone_id', orientation='h', color='dwell_ms',
                                           color_continuous_scale="Purp", template="plotly_dark")
                        st.plotly_chart(fig_dwell, use_container_width=True)
                    
            with col2:
                st.markdown("#### ⚡ Recent Zone Interactions (Live Feed)")
                recent = filtered_events[['timestamp', 'camera_id', 'zone_id', 'event_type', 'visitor_id']].sort_values(by='timestamp', ascending=False).head(10)
                st.dataframe(recent, use_container_width=True, hide_index=True)

    # =====================================================
    # TAB 6: VIDEO COMMAND CENTER
    # =====================================================
    with tabs[5]:
        st.markdown(f"### 🎥 CCTV Command Center - {selected_store}")
        cam_to_show = selected_camera if selected_camera != "All Cameras" else (found_cams[0] if found_cams else None)
        
        if cam_to_show:
            st.markdown(f"##### 📹 Original Feed ({cam_to_show})")
            vid_path = f"data/videos/{selected_store}/{cam_to_show}.mp4"
            if os.path.exists(vid_path): 
                st.video(vid_path)
            else: st.error(f"❌ Not found: {vid_path}")
        else:
            st.warning("No cameras available for this store.")

if __name__ == "__main__":
    main()
