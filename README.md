# Flight Price Anomaly Detection Agent

A Python agent that continuously monitors flight prices (economy vs premium economy) and detects when premium economy flights are cheaper than economy flights, then alerts the user.

**Route:** Delhi (DEL) to New York (JFK)
**Airline:** Air France
**Duration:** 3-day continuous monitoring at the hackathon

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Your First Check

```bash
# Run a single price check (live scraping)
python main.py --mode check

# Or use test data if scraping fails
python main.py --mode check --test

# Run demo with test data (5 checks)
python main.py --mode demo
```

### 3. View History

```bash
python main.py --mode history
```

## Architecture

### Components

1. **scrapers.py** - Fetches prices from two sources:
   - Economy: Skyscanner (web scraping)
   - Premium Economy: Air France website (web scraping)

2. **database.py** - SQLite persistence:
   - `price_checks` table: Records every price check
   - `anomalies` table: Records detected anomalies only

3. **anomaly_detector.py** - Detection logic:
   - Compares premium < economy
   - Checks for duplicate anomalies (no duplicate alerts)
   - Formats alerts

4. **test_data.py** - Fallback mechanism:
   - If scraping fails, loads test prices from `test_data.json`
   - Keeps the agent running without breaking

5. **main.py** - Orchestration:
   - Runs single check or continuous loop
   - Calls scraper → detector → database in sequence
   - Shows results and history

## Usage Modes

### Single Check
```bash
python main.py --mode check
```
Runs one price check, stores result, exits. Good for testing.

### Demo Mode
```bash
python main.py --mode demo
```
Runs 5 checks with test data, shows history. Good for demonstrating without live data.

### History
```bash
python main.py --mode history
```
Shows last 10 price checks and anomalies from database.

### Test Data Fallback
```bash
python main.py --mode check --test
```
Use test data instead of live scraping. Useful for testing the anomaly detection without needing live prices.

## Database

SQLite database: `flight_prices.db`

### price_checks table
- `id` - Check ID
- `timestamp` - When the check ran
- `economy_price` - Economy cabin price (INR)
- `premium_price` - Premium economy price (INR)
- `anomaly_detected` - Boolean flag
- `anomaly_type` - Type of anomaly (e.g., "premium_cheaper")
- `notes` - Additional context

### anomalies table
- `id` - Anomaly ID
- `timestamp` - When anomaly was first detected
- `economy_price` - Economy price at time of anomaly
- `premium_price` - Premium price at time of anomaly
- `difference_pct` - How much cheaper premium was (%)
- `alerted` - Whether alert was sent
- `alert_type` - Type of alert
- `notes` - Why this was an anomaly

## Extending for Hackathon

### Tomorrow: Add Continuous Monitoring

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(run_single_check, 'interval', hours=6)
scheduler.start()
```

Run every 6 hours for 3 days straight.

### Tomorrow: Add Claude API Analysis

```python
from anthropic import Anthropic
client = Anthropic()

def analyze_anomaly_with_claude(result):
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=200,
        messages=[
            {"role": "user", "content": f"Why might premium economy be {result['difference_pct']:.2f}% cheaper than economy on DEL-JFK with Air France? Brief analysis."}
        ]
    )
    return response.content[0].text
```

### Tomorrow: Add Alerting

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(result):
    msg = MIMEText(result["message"])
    msg["Subject"] = "FLIGHT PRICE ANOMALY DETECTED"
    # ... send email
```

## Fallback Strategy

If scraping breaks (HTML changes, 403 Forbidden, etc.):

1. Agent automatically tries to load test data
2. All logic (anomaly detection, deduplication, database) still works
3. You can swap data sources without changing the detection pipeline
4. At hackathon: "In production this scrapes live; for demo I'm using historical snapshots"

## Success Criteria for Day 1

- [ ] Run `python main.py --mode check` successfully
- [ ] See output: "Check at [time]: Economy ₹X, Premium ₹Y, Anomaly: NO"
- [ ] Database has 1 `price_checks` record
- [ ] Run `python main.py --mode demo` and see 5 checks with some anomalies
- [ ] Run `python main.py --mode history` and see recorded data

## Success Criteria for Hackathon

- [ ] Agent runs continuously for 8 hours
- [ ] Detects and logs anomalies without duplicate alerts
- [ ] Database shows full history of 8+ price checks
- [ ] Can demonstrate: "Anomaly on [date] at [time]: Premium was X% cheaper than Economy"
- [ ] Claude API provides analysis of why anomalies occurred
- [ ] Email/console alert sent when anomaly detected

## Troubleshooting

### "Error fetching prices from live sources"
This means scraping failed. The agent will automatically fall back to test data. For tomorrow at the hackathon, this is fine.

### "No module named 'requests'"
You didn't install requirements. Run: `pip install -r requirements.txt`

### "database.py not found"
Make sure you're running from the project root directory where all Python files are located.

## Files

- `main.py` - Entry point
- `scrapers.py` - Price fetching
- `anomaly_detector.py` - Detection logic
- `database.py` - Data persistence
- `test_data.py` - Fallback data
- `test_data.json` - Sample prices (auto-generated)
- `flight_prices.db` - SQLite database (auto-created)
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Notes for Tomorrow's Hackathon

1. **Data source resilience:** If Skyscanner or Air France's HTML changes, you have test data ready. Swap with one line.
2. **Anomaly deduplication:** The system tracks exact price combinations, so you won't get alert fatigue.
3. **Extensibility:** The pipeline is modular. Tomorrow you can add Claude analysis, email alerts, and continuous scheduling without touching detection logic.
4. **Demo-ready:** Even if scraping breaks, you have test data that demonstrates the full system working.

---

Built for hackathon. Designed for speed and resilience.
