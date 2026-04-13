---
name: meta-stock
description: Calculate the monthly average of Meta's stock price. Use when the user asks about Meta stock averages or META stock analysis.
disable-model-invocation: false
allowed-tools: WebFetch Bash
---

# Meta Stock Monthly Average Calculator

Calculate the monthly average closing price for Meta Platforms (META) stock.

## Instructions

1. **Fetch stock data**: Use the `yfinance` Python library to download META historical stock data for the requested period. If no period is specified, default to the last 12 months.

2. **Calculate monthly averages**: Group the daily closing prices by month and compute the average closing price for each month.

3. **Present results**: Display a clean table with:
   - Month (YYYY-MM format)
   - Average closing price (rounded to 2 decimal places)
   - Monthly high
   - Monthly low
   - Number of trading days

4. **Handle arguments**:
   - `$ARGUMENTS` may contain a date range like "2024-01 to 2024-06" or a period like "last 6 months"
   - If no arguments, use the last 12 months

## Example Usage

- `/meta-stock` - Last 12 months of monthly averages
- `/meta-stock 2024-01 to 2024-12` - Monthly averages for 2024
- `/meta-stock last 3 months` - Last 3 months

## Implementation

Run the following Python script (adjust dates based on user input):

```python
import subprocess, sys
try:
    import yfinance as yf
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "--break-system-packages", "-q"])
    import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Download META stock data
ticker = yf.Ticker("META")
# Adjust start/end based on user arguments
hist = ticker.history(period="1y")

# Group by month and calculate statistics
monthly = hist.groupby(hist.index.to_period('M')).agg(
    avg_close=('Close', 'mean'),
    high=('High', 'max'),
    low=('Low', 'min'),
    trading_days=('Close', 'count')
).round(2)

print("\nMETA Monthly Stock Averages")
print("=" * 65)
print(f"{'Month':<12} {'Avg Close':>10} {'High':>10} {'Low':>10} {'Days':>6}")
print("-" * 65)
for period, row in monthly.iterrows():
    print(f"{str(period):<12} ${row['avg_close']:>9.2f} ${row['high']:>9.2f} ${row['low']:>9.2f} {int(row['trading_days']):>6}")
print("=" * 65)
```
