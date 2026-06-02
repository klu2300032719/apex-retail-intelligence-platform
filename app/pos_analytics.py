import sqlite3
import pandas as pd
import numpy as np
import datetime
import os

DB_PATH = 'store_analytics.db'
POS_FILE = 'data/layouts/Brigade_Bangalore_10_April_26 (1)bc6219c.csv'

# ==============================================================================
# ZONE TO BRAND MAPPING
# Matches CCTV polygon zones to actual Retail Brands in the POS system
# ==============================================================================
ZONE_BRAND_MAP = {
    "MAYBELLINE_ZONE": "Maybelline",
    "LAKME_ZONE": "Lakme",
    "FACESCANADA_ZONE": "Faces Canada",
    "SWISS_BEAUTY_ZONE": "Swiss Beauty",
    "DERMA_CO_ZONE": "The Derma Co",
    "THE_FACE_SHOP_ZONE": "The Face Shop",
    "COSRX_ZONE": "COSRX",
    "MINIMALIST_ZONE": "Minimalist",
    "FARMSTAY_ZONE": "Farmstay"
}

def setup_database_tables():
    """Creates the necessary POS and AI SQLite tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. POS Transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pos_transactions (
            order_id TEXT,
            invoice_number TEXT,
            order_date TEXT,
            order_time TEXT,
            product_name TEXT,
            brand_name TEXT,
            sub_category TEXT,
            qty INTEGER,
            total_amount REAL,
            customer_number TEXT,
            salesperson_name TEXT
        )
    ''')
    
    # 2. Sales Analytics (Aggregated)
    cursor.execute('DROP TABLE IF EXISTS sales_analytics')
    cursor.execute('''
        CREATE TABLE sales_analytics (
            metric_name TEXT PRIMARY KEY,
            metric_value TEXT,
            last_updated TEXT
        )
    ''')
    
    # 3. Zone Conversion (Linking CCTV to POS)
    cursor.execute('DROP TABLE IF EXISTS zone_conversion')
    cursor.execute('''
        CREATE TABLE zone_conversion (
            zone_name TEXT PRIMARY KEY,
            brand_name TEXT,
            total_engagements INTEGER,
            total_purchases INTEGER,
            conversion_rate REAL,
            revenue_generated REAL
        )
    ''')
    
    # 4. AI Insights
    cursor.execute('DROP TABLE IF EXISTS ai_insights')
    cursor.execute('''
        CREATE TABLE ai_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            insight_text TEXT,
            severity TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def process_pos_data():
    """Loads and cleans the REAL POS CSV dataset."""
    if not os.path.exists(POS_FILE):
        print(f"[ERROR] Real POS file not found at {POS_FILE}")
        return pd.DataFrame()
        
    df = pd.read_csv(POS_FILE)
    
    # Clean Data
    df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0.0)
    df['qty'] = pd.to_numeric(df['qty'], errors='coerce').fillna(1).astype(int)
    
    # The real CSV has 'order_date' (dd/mm/yyyy maybe) and 'order_time'
    df['order_datetime'] = pd.to_datetime(df['order_date'] + ' ' + df['order_time'], errors='coerce', dayfirst=True)
    
    # Save raw transactions to SQLite
    conn = sqlite3.connect(DB_PATH)
    
    columns_to_keep = ['order_id', 'invoice_number', 'order_date', 'order_time', 'product_name', 'brand_name', 'sub_category', 'qty', 'total_amount', 'customer_number', 'salesperson_name']
    df_sql = df[[c for c in columns_to_keep if c in df.columns]].copy()
    
    df_sql.to_sql('pos_transactions', conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"[INFO] Successfully ingested {len(df)} REAL POS transactions.")
    return df

def generate_business_analytics(df_pos):
    """Calculates Revenue, Peak Hours, Top Brands, etc."""
    if df_pos.empty: return
    metrics = {}
    
    # Revenue metrics
    metrics['total_revenue'] = df_pos['total_amount'].sum()
    metrics['avg_basket_value'] = df_pos.groupby('invoice_number')['total_amount'].sum().mean()
    
    # Top Brand & Category
    top_brand = df_pos.groupby('brand_name')['total_amount'].sum().idxmax()
    metrics['top_selling_brand'] = top_brand
    
    top_cat = df_pos.groupby('sub_category')['total_amount'].sum().idxmax()
    metrics['top_selling_category'] = top_cat
    
    # Peak Hours
    if not df_pos['order_datetime'].isnull().all():
        df_pos['hour'] = df_pos['order_datetime'].dt.hour
        peak_hour = df_pos['hour'].mode().iloc[0]
        metrics['peak_sales_hour'] = f"{int(peak_hour):02d}:00"
    
    # Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    for k, v in metrics.items():
        if isinstance(v, float): v = round(v, 2)
        cursor.execute("INSERT OR REPLACE INTO sales_analytics (metric_name, metric_value, last_updated) VALUES (?, ?, ?)", (k, str(v), now))
    conn.commit()
    conn.close()
    print("[INFO] Business analytics generated from REAL POS data.")

def build_conversion_intelligence(df_pos):
    """Correlates CCTV zone engagements with actual POS Brand purchases."""
    if df_pos.empty: return
    conn = sqlite3.connect(DB_PATH)
    
    try:
        df_events = pd.read_sql("SELECT * FROM events", conn)
    except sqlite3.OperationalError:
        print("[WARNING] events table not found. Run event_generator.py first.")
        df_events = pd.DataFrame(columns=['zone', 'event_type'])
    
    insights = []
    zone_stats = []
    
    brand_revenue = df_pos.groupby('brand_name')['total_amount'].sum().to_dict()
    brand_purchases = df_pos.groupby('brand_name')['invoice_number'].nunique().to_dict()
    
    for zone, brand in ZONE_BRAND_MAP.items():
        # Total CCTV Engagements (ZONE_ENTER)
        engagements = len(df_events[(df_events['zone'] == zone) & (df_events['event_type'].isin(['ZONE_ENTER', 'ENTRY', 'REENTRY']))])
        
        purchases = brand_purchases.get(brand, 0)
        revenue = brand_revenue.get(brand, 0.0)
        
        # Proper conversion rate logic
        # conversion_rate = (total_purchases / max(total_engagements, 1)) * 100, capped at 100%
        raw_conv = (purchases / max(engagements, 1)) * 100
        conv_rate = min(raw_conv, 100.0)
        
        # Identify Insufficient Data
        if engagements < 5:
            # Not enough CCTV data to prove a realistic conversion rate
            conv_rate = 0.0
            
        zone_stats.append((zone, brand, engagements, purchases, round(conv_rate, 2), revenue))
        
        # Automatic AI Insights generation based on logic
        if engagements > 20 and conv_rate < 5.0:
            insights.append(("OPTIMIZATION", f"High engagement but low conversion ({conv_rate:.1f}%) in {zone}. Check pricing or product availability.", "WARNING"))
        elif conv_rate > 20.0:
            insights.append(("PERFORMANCE", f"The {zone} ({brand}) is converting highly efficiently ({conv_rate:.1f}%). Keep stock replenished.", "SUCCESS"))
            
    # Insert Zone Conversions
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT OR REPLACE INTO zone_conversion 
        (zone_name, brand_name, total_engagements, total_purchases, conversion_rate, revenue_generated)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', zone_stats)
    
    # Analyze Queue Congestion (from events)
    queue_joins = len(df_events[df_events['event_type'] == 'BILLING_QUEUE_JOIN'])
    queue_abandons = len(df_events[df_events['event_type'] == 'BILLING_QUEUE_ABANDON'])
    if queue_joins > 0:
        abandon_rate = queue_abandons / queue_joins
        if abandon_rate > 0.15:
            insights.append(("STAFFING", f"Queue congestion is actively causing a {abandon_rate*100:.1f}% checkout abandonment rate. Recommend additional staffing.", "CRITICAL"))
            
    # Insert peak sales insights
    peak_hour = None
    if not df_pos['order_datetime'].isnull().all():
        peak_hour = df_pos['order_datetime'].dt.hour.mode().iloc[0]
        insights.append(("STAFFING", f"Peak sales occur between {int(peak_hour)}:00 and {int(peak_hour)+1}:00. Ensure maximum cashier availability.", "INFO"))
            
    # Insert AI Insights
    for cat, text, severity in insights:
        cursor.execute("INSERT INTO ai_insights (category, insight_text, severity) VALUES (?, ?, ?)", (cat, text, severity))
        
    conn.commit()
    conn.close()
    print("[INFO] Conversion Intelligence and AI Insights generated.")

def main():
    print("="*60)
    print("RUNNING POS ANALYTICS & CONVERSION ENGINE (REAL DATA)")
    print("="*60)
    setup_database_tables()
    df_pos = process_pos_data()
    generate_business_analytics(df_pos)
    build_conversion_intelligence(df_pos)
    print("="*60)
    print("PIPELINE COMPLETE. Launch dashboard.py to view metrics.")

if __name__ == "__main__":
    main()
