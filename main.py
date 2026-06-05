#!/usr/bin/env python3
"""
Flight Price Anomaly Detection Agent
Main entry point. Runs one or continuous price checks.
"""

import sys
import argparse
from datetime import datetime
import time

import database
import scrapers
import anomaly_detector
import test_data

# Global test data provider - created once and reused
_test_provider = None

def get_test_provider():
    """Get or create the singleton test data provider."""
    global _test_provider
    if _test_provider is None:
        _test_provider = test_data.TestDataProvider()
    return _test_provider

def run_single_check(use_test_data=False):
    """Run a single price check cycle."""
    print(f"\n{'='*70}")
    print(f"Price Check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    if use_test_data:
        print("Using TEST DATA (fallback mode)")
        provider = get_test_provider()
        economy_price, premium_price = provider.get_next()
        print(f"Loaded test prices: Economy ₹{economy_price}, Premium ₹{premium_price}")
    else:
        print("Fetching live prices...")
        economy_price, premium_price = scrapers.fetch_both_prices("DEL", "JFK")
        
        if not scrapers.validate_prices(economy_price, premium_price):
            print("ERROR: Could not fetch valid prices from live sources")
            print("Falling back to test data...")
            provider = get_test_provider()
            economy_price, premium_price = provider.get_next()
    
    if economy_price is None or premium_price is None:
        print("FATAL: No valid price data available")
        return False
    
    result = anomaly_detector.process_check(economy_price, premium_price)
    
    print(result["message"])
    
    stats = database.get_summary_stats()
    print(f"\nDatabase stats: {stats['total_checks']} total checks, {stats['total_anomalies']} anomalies logged")
    
    if result["is_anomaly"] and result["is_new"]:
        print("\n" + "!"*70)
        print("ALERT: NEW ANOMALY DETECTED")
        print("!"*70)
        return True
    
    return False

def show_history(limit=10):
    """Show recent price checks."""
    print(f"\n{'='*70}")
    print(f"Recent Price Checks (last {limit})")
    print(f"{'='*70}")
    
    checks = database.get_all_checks()[:limit]
    
    if not checks:
        print("No price checks recorded yet")
        return
    
    for check in checks:
        check_id, timestamp, economy, premium, currency, anomaly, anomaly_type, notes = check
        status = "ANOMALY" if anomaly else "normal"
        print(f"{timestamp} | Economy ₹{economy:.0f} | Premium ₹{premium:.0f} | {status}")
    
    print(f"\n{'='*70}")
    print(f"Recent Anomalies")
    print(f"{'='*70}")
    
    anomalies = database.get_all_anomalies()[:limit]
    
    if not anomalies:
        print("No anomalies recorded yet")
        return
    
    for anomaly in anomalies:
        anom_id, timestamp, economy, premium, diff_pct, alerted, alert_type, notes = anomaly
        print(f"{timestamp} | Economy ₹{economy:.0f} | Premium ₹{premium:.0f} | Diff: {diff_pct:.2f}%")

def main():
    parser = argparse.ArgumentParser(
        description="Flight Price Anomaly Detection Agent"
    )
    parser.add_argument(
        "--mode",
        choices=["check", "history", "demo"],
        default="check",
        help="Mode: check (run one price check), history (show recent checks), demo (run with test data)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use test data instead of live scraping"
    )
    
    args = parser.parse_args()
    
    database.init_db()
    
    if args.mode == "check":
        run_single_check(use_test_data=args.test)
    
    elif args.mode == "history":
        show_history()
    
    elif args.mode == "demo":
        print("DEMO MODE: Running with test data")
        test_data.create_test_data()
        
        for i in range(5):
            print(f"\n[Check {i+1}/5]")
            run_single_check(use_test_data=True)
            if i < 4:
                time.sleep(1)
        
        show_history()

if __name__ == "__main__":
    main()
