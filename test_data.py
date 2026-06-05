import json
from pathlib import Path
import random

TEST_DATA_FILE = "test_data.json"

def create_test_data():
    """
    Create realistic test data with some anomalies included.
    Saves to test_data.json.
    """
    test_checks = [
        {"economy": 45000, "premium": 48000, "label": "Normal pricing"},
        {"economy": 46500, "premium": 49200, "label": "Normal pricing"},
        {"economy": 44800, "premium": 42500, "label": "ANOMALY: Premium cheaper"},
        {"economy": 47000, "premium": 50100, "label": "Normal pricing"},
        {"economy": 45500, "premium": 45200, "label": "ANOMALY: Premium slightly cheaper"},
        {"economy": 48000, "premium": 51200, "label": "Normal pricing"},
        {"economy": 46000, "premium": 49500, "label": "Normal pricing"},
        {"economy": 45200, "premium": 43800, "label": "ANOMALY: Premium cheaper"},
        {"economy": 47500, "premium": 50800, "label": "Normal pricing"},
        {"economy": 44500, "premium": 44200, "label": "ANOMALY: Premium slightly cheaper"},
        {"economy": 46800, "premium": 49900, "label": "Normal pricing"},
        {"economy": 45700, "premium": 48200, "label": "Normal pricing"},
    ]
    
    with open(TEST_DATA_FILE, 'w') as f:
        json.dump(test_checks, f, indent=2)
    
    print(f"Test data created: {TEST_DATA_FILE}")
    return test_checks

def load_test_data():
    """Load test data from file. Create if doesn't exist."""
    if not Path(TEST_DATA_FILE).exists():
        return create_test_data()
    
    with open(TEST_DATA_FILE, 'r') as f:
        return json.load(f)

def get_next_test_price():
    """Generator that yields test prices one by one."""
    test_data = load_test_data()
    for check in test_data:
        yield check["economy"], check["premium"]

class TestDataProvider:
    """Provides test prices in order, cycling through all entries."""
    
    def __init__(self):
        self.test_data = load_test_data()
        self.index = 0
        print(f"[TEST-DATA] Loaded {len(self.test_data)} test price pairs")
    
    def get_next(self):
        """Get next test price pair. Cycles through all data."""
        # Get current entry
        check = self.test_data[self.index]
        economy = check["economy"]
        premium = check["premium"]
        label = check["label"]
        
        print(f"[TEST-DATA] Check {self.index}/{len(self.test_data)}: {label} - Economy ₹{economy}, Premium ₹{premium}")
        
        # Increment and wrap around
        self.index = (self.index + 1) % len(self.test_data)
        
        return economy, premium
    
    def reset(self):
        """Reset to beginning."""
        self.index = 0
        print(f"[TEST-DATA] Reset to index 0")
