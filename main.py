#!/usr/bin/env python3
"""
Flight Price Anomaly Detection Agent
Main entry point. Runs one or continuous price checks.
"""

import sys
import argparse
from datetime import datetime
import time
import os

from apscheduler.schedulers.background import BackgroundScheduler

import database
import scrapers
import anomaly_detector
import test_data

# Global test data provider - created once and reused
_test_provider = None
scheduler = None

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
        anom_id, timestamp, economy, premium, diff_pct, alerted, alert_type, notes, analysis = anomaly
        print(f"{timestamp} | Economy ₹{economy:.0f} | Premium ₹{premium:.0f} | Diff: {diff_pct:.2f}%")
        if analysis:
            print(f"Analysis: {analysis}\n")

def schedule_continuous_checks(use_test_data=False, interval_minutes=15, duration_minutes=None):
    """Start background scheduler for continuous price checks."""
    global scheduler
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=run_single_check,
        args=(use_test_data,),
        trigger="interval",
        minutes=interval_minutes,
        id="price_check_job",
        name="Price Check Job",
        replace_existing=True
    )
    
    scheduler.start()
    print(f"\nScheduler started. Running price checks every {interval_minutes} minute(s).")
    print("Press Ctrl+C to stop.\n")
    
    start_time = time.time()
    try:
        while True:
            time.sleep(1)
            
            if duration_minutes:
                elapsed = (time.time() - start_time) / 60
                if elapsed >= duration_minutes:
                    print(f"\nDuration limit ({duration_minutes} minutes) reached. Shutting down...")
                    break
    except KeyboardInterrupt:
        print("\nShutting down scheduler...")
    finally:
        scheduler.shutdown()
        show_history()

def main():
    parser = argparse.ArgumentParser(
        description="Flight Price Anomaly Detection Agent"
    )
    parser.add_argument(
        "--mode",
        choices=["check", "history", "demo", "continuous"],
        default="check",
        help="Mode: check (single check), history (show recent), demo (5 test checks), continuous (scheduled checks)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use test data instead of live scraping"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Interval in minutes for continuous mode (default: 15)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Run for specified number of minutes, then auto-stop (optional)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "demo":
        if os.path.exists("flight_prices.db"):
            os.remove("flight_prices.db")
        print("DEMO MODE: Running with test data")
        database.init_db()
        test_data.create_test_data()
        
        for i in range(5):
            print(f"\n[Check {i+1}/5]")
            run_single_check(use_test_data=True)
            if i < 4:
                time.sleep(1)
        
        show_history()
    
    elif args.mode == "continuous":
        database.init_db()
        print("Running initial price check...")
        run_single_check(use_test_data=args.test)
        schedule_continuous_checks(use_test_data=args.test, interval_minutes=args.interval, duration_minutes=args.duration)
    
    else:
        database.init_db()
        
        if args.mode == "check":
            run_single_check(use_test_data=args.test)
        
        elif args.mode == "history":
            show_history()

if __name__ == "__main__":
    main()