from datetime import datetime
import database

DEBUG = True

def log_debug(msg):
    """Print debug message with timestamp."""
    if DEBUG:
        print(f"[DEBUG-ANOMALY] {msg}")

def detect_anomaly(economy_price, premium_price):
    """
    Detect if premium economy is cheaper than economy.
    Returns (is_anomaly, difference_pct, message).
    """
    log_debug(f"Comparing: Economy ₹{economy_price} vs Premium ₹{premium_price}")
    
    if economy_price is None or premium_price is None:
        log_debug("Cannot detect: missing price data")
        return False, 0, "Cannot detect: missing price data"
    
    if economy_price <= 0 or premium_price <= 0:
        log_debug("Cannot detect: invalid prices (<=0)")
        return False, 0, "Cannot detect: invalid prices"
    
    difference = economy_price - premium_price
    difference_pct = (difference / economy_price) * 100 if economy_price > 0 else 0
    
    is_anomaly = premium_price < economy_price
    
    log_debug(f"Difference: ₹{difference:.2f} ({difference_pct:.2f}%)")
    log_debug(f"Anomaly detected: {is_anomaly}")
    
    if is_anomaly:
        message = f"ANOMALY DETECTED: Premium (₹{premium_price:.2f}) is ₹{difference:.2f} ({difference_pct:.2f}%) cheaper than Economy (₹{economy_price:.2f})"
    else:
        message = f"No anomaly: Economy ₹{economy_price:.2f}, Premium ₹{premium_price:.2f}"
    
    return is_anomaly, difference_pct, message

def is_new_anomaly(economy_price, premium_price):
    """
    Check if this anomaly has not been reported before.
    Returns True if it's a new anomaly, False if we've already logged it.
    """
    log_debug(f"Checking if anomaly is new: Economy ₹{economy_price}, Premium ₹{premium_price}")
    
    exists = database.check_if_anomaly_exists(economy_price, premium_price)
    
    if exists:
        log_debug("DUPLICATE: This exact price pair has been reported before")
        return False
    else:
        log_debug("NEW: This is a previously unseen anomaly")
        return True

def process_check(economy_price, premium_price):
    """
    Full pipeline: detect anomaly, check if new, log to database, return results.
    Returns dict with check details.
    """
    log_debug("=== PROCESSING PRICE CHECK ===")
    
    is_anomaly, diff_pct, message = detect_anomaly(economy_price, premium_price)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "economy_price": economy_price,
        "premium_price": premium_price,
        "is_anomaly": is_anomaly,
        "difference_pct": diff_pct,
        "message": message,
        "is_new": False,
        "saved_to_db": False
    }
    
    log_debug(f"Saving price check to database: {economy_price}, {premium_price}, anomaly={is_anomaly}")
    price_check_id = database.save_price_check(
        economy_price, 
        premium_price, 
        anomaly_detected=is_anomaly,
        anomaly_type="premium_cheaper" if is_anomaly else None
    )
    result["saved_to_db"] = True
    log_debug(f"Price check saved with ID: {price_check_id}")
    
    if is_anomaly:
        log_debug("Anomaly detected - checking if it's new...")
        if is_new_anomaly(economy_price, premium_price):
            result["is_new"] = True
            log_debug("NEW ANOMALY - Saving to anomalies table and would send alert")
            anomaly_id = database.save_anomaly(
                economy_price,
                premium_price,
                diff_pct,
                alert_type="price_inversion",
                notes=f"Premium economy cheaper than economy by {diff_pct:.2f}%"
            )
            result["anomaly_id"] = anomaly_id
            log_debug(f"Anomaly saved with ID: {anomaly_id}")
            result["message"] += " [NEW ANOMALY - ALERT]"
        else:
            log_debug("DUPLICATE ANOMALY - Not sending alert again")
            result["message"] += " [DUPLICATE - NOT ALERTING]"
    
    log_debug("=== PROCESSING COMPLETE ===")
    return result

def format_alert(result):
    """Format anomaly detection result for console output."""
    timestamp = result["timestamp"]
    economy = result["economy_price"]
    premium = result["premium_price"]
    
    if result["is_anomaly"] and result["is_new"]:
        return f"\n{'='*70}\n[ALERT] {timestamp}\n{result['message']}\n{'='*70}\n"
    elif result["is_anomaly"]:
        return f"[DUPLICATE] {timestamp}: Anomaly already logged\n"
    else:
        return f"[{timestamp}] Economy ₹{economy:.2f}, Premium ₹{premium:.2f} - No anomaly\n"
