import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = "flight_prices.db"

def init_db():
    """Initialize database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            economy_price REAL NOT NULL,
            premium_price REAL NOT NULL,
            currency TEXT DEFAULT 'INR',
            anomaly_detected BOOLEAN DEFAULT 0,
            anomaly_type TEXT,
            notes TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            economy_price REAL NOT NULL,
            premium_price REAL NOT NULL,
            difference_pct REAL NOT NULL,
            alerted BOOLEAN DEFAULT 0,
            alert_type TEXT,
            notes TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def save_price_check(economy_price, premium_price, anomaly_detected=False, anomaly_type=None, notes=None):
    """Save a price check to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO price_checks (economy_price, premium_price, anomaly_detected, anomaly_type, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (economy_price, premium_price, anomaly_detected, anomaly_type, notes))
    
    conn.commit()
    price_check_id = cursor.lastrowid
    conn.close()
    
    return price_check_id

def save_anomaly(economy_price, premium_price, difference_pct, alert_type=None, notes=None):
    """Save an anomaly to the anomalies table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO anomalies (economy_price, premium_price, difference_pct, alert_type, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (economy_price, premium_price, difference_pct, alert_type, notes))
    
    conn.commit()
    anomaly_id = cursor.lastrowid
    conn.close()
    
    return anomaly_id

def get_last_check():
    """Get the last price check from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM price_checks ORDER BY timestamp DESC LIMIT 1
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    return result

def get_all_checks():
    """Get all price checks."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM price_checks ORDER BY timestamp DESC")
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_all_anomalies():
    """Get all anomalies."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM anomalies ORDER BY timestamp DESC")
    results = cursor.fetchall()
    conn.close()
    
    return results

def check_if_anomaly_exists(economy_price, premium_price):
    """Check if this exact anomaly already exists in the last 24 hours."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id FROM anomalies 
        WHERE economy_price = ? AND premium_price = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (economy_price, premium_price))
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

def get_summary_stats():
    """Get summary statistics from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM price_checks")
    total_checks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM anomalies")
    total_anomalies = cursor.fetchone()[0]
    
    conn.close()
    
    return {"total_checks": total_checks, "total_anomalies": total_anomalies}
