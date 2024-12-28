import requests
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
import matplotlib.pyplot as plt

# Step 1: Define your API Key, Ticker, and Initial Balance
API_KEY = "kNC1GSQ9nayON7oiIxts48lDBPp357Mj"  # Replace with your Polygon.io API key
TICKER = "TSLA"
INITIAL_BALANCE = 100000  # Starting balance in USD


# Step 2: Fetch historical minute-level data from Polygon.io
def fetch_polygon_data(ticker, multiplier, timespan, from_date, to_date):
    """
    Fetch historical minute-level candlestick data from Polygon.io.
    """
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
    params = {
        "apiKey": API_KEY,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "results" in data:
            df = pd.DataFrame(data["results"])
            # Format the data
            df["timestamp"] = pd.to_datetime(
                df["t"], unit="ms"
            )  # Convert UNIX time to datetime
            df.set_index("timestamp", inplace=True)  # Set timestamp as the index
            df.rename(
                columns={
                    "o": "Open",
                    "h": "High",
                    "l": "Low",
                    "c": "Close",
                    "v": "Volume",
                },
                inplace=True,
            )
            return df[["Open", "High", "Low", "Close", "Volume"]]
        else:
            raise ValueError("No data found in the response.")
    else:
        raise ValueError(
            f"Error fetching data: {response.status_code}, {response.text}"
        )


# Fetch data for the past 7 days (minute-level data)
from_date = "2024-12-01"  # Start date (YYYY-MM-DD)
to_date = "2024-12-27"  # End date (YYYY-MM-DD)
data = fetch_polygon_data(
    TICKER, multiplier=1, timespan="minute", from_date=from_date, to_date=to_date
)

# Step 3: Clean and preprocess the data
data.dropna(inplace=True)

# Step 4: Add Technical Indicators (EMA and RSI)
data["EMA9"] = EMAIndicator(data["Close"], window=9).ema_indicator()
data["EMA21"] = EMAIndicator(data["Close"], window=21).ema_indicator()
data["RSI"] = RSIIndicator(data["Close"], window=14).rsi()

# Step 5: Define Buy/Sell Signals
data["Buy_Signal"] = (
    (data["EMA9"] > data["EMA21"]) & (data["RSI"] > 30) & (data["RSI"] < 70)
)
data["Sell_Signal"] = (
    (data["EMA9"] < data["EMA21"]) | (data["RSI"] > 70) | (data["RSI"] < 30)
)

# Step 6: Simulate Paper Trading
balance = INITIAL_BALANCE
shares_held = 0
trade_log = []

for index, row in data.iterrows():
    price = row["Close"]
    # Handle Buy Signal
    if row["Buy_Signal"] and balance > 0:
        shares_to_buy = balance // price  # Buy as many shares as possible
        if shares_to_buy > 0:
            cost = shares_to_buy * price
            balance -= cost
            shares_held += shares_to_buy
            trade_log.append((index, "BUY", shares_to_buy, price, balance))

    # Handle Sell Signal
    elif row["Sell_Signal"] and shares_held > 0:
        revenue = shares_held * price
        balance += revenue
        trade_log.append((index, "SELL", shares_held, price, balance))
        shares_held = 0


# Step 7: Print Trade Log
for trade in trade_log:
    print(
        f"{trade[0]}: {trade[1]} {trade[2]} shares at ${trade[3]:.2f}, Balance: ${trade[4]:.2f}"
    )

# Step 8: Calculate Final Balance
final_balance = balance + (shares_held * data.iloc[-1]["Close"])
print(f"Final Balance: ${final_balance:.2f}")
print(f"Net Profit: ${final_balance - INITIAL_BALANCE:.2f}")

# Step 9: Plot the Results
plt.figure(figsize=(14, 8))
plt.plot(data.index, data["Close"], label="Close Price", color="blue")
plt.plot(data.index, data["EMA9"], label="EMA9", color="green", linestyle="--")
plt.plot(data.index, data["EMA21"], label="EMA21", color="red", linestyle="--")

# Plot Buy and Sell Signals
buy_signals = data[data["Buy_Signal"]]
sell_signals = data[data["Sell_Signal"]]
plt.scatter(
    buy_signals.index,
    buy_signals["Close"],
    label="Buy Signal",
    marker="^",
    color="green",
    alpha=1,
)
plt.scatter(
    sell_signals.index,
    sell_signals["Close"],
    label="Sell Signal",
    marker="v",
    color="red",
    alpha=1,
)

plt.title(f"Scalping Strategy with Paper Trading for {TICKER}")
plt.xlabel("Date")
plt.ylabel("Price")
plt.legend()
plt.grid()
plt.show()
