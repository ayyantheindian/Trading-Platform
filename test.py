import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from itertools import product

# Step 1: Define Constants
API_KEY = "kNC1GSQ9nayON7oiIxts48lDBPp357Mj"  # Replace with your Polygon.io API key
TICKER = "TSLA"
INITIAL_BALANCE = 100000  # Starting balance in USD
EMA_WINDOWS = [(5, 20), (9, 21), (12, 26)]  # EMA pairs to test
RSI_THRESHOLDS = [(40, 60), (30, 70), (35, 65)]  # RSI overbought/oversold levels


# Step 2: Fetch Historical Data from Polygon.io
def fetch_polygon_data(ticker, multiplier, timespan, from_date, to_date):
    """
    Fetch historical minute-level candlestick data from Polygon.io.
    """
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
    params = {"apiKey": API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "results" in data:
            df = pd.DataFrame(data["results"])
            df["timestamp"] = pd.to_datetime(
                df["t"], unit="ms"
            )  # Convert UNIX time to datetime
            df.set_index("timestamp", inplace=True)
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


# Fetch historical data
from_date = "2024-12-01"  # Start date (YYYY-MM-DD)
to_date = "2024-12-27"  # End date (YYYY-MM-DD)
data = fetch_polygon_data(
    TICKER, multiplier=1, timespan="minute", from_date=from_date, to_date=to_date
)


# Step 3: Backtest Scalping Strategy
def backtest_scalping(data, ema_short, ema_long, rsi_lower, rsi_upper):
    """
    Backtest the scalping strategy with given parameters.
    """
    data["EMA_Short"] = EMAIndicator(data["Close"], window=ema_short).ema_indicator()
    data["EMA_Long"] = EMAIndicator(data["Close"], window=ema_long).ema_indicator()
    data["RSI"] = RSIIndicator(data["Close"], window=14).rsi()

    data["Buy_Signal"] = (
        (data["EMA_Short"] > data["EMA_Long"])
        & (data["RSI"] > rsi_lower)
        & (data["RSI"] < rsi_upper)
    )
    data["Sell_Signal"] = (
        (data["EMA_Short"] < data["EMA_Long"])
        | (data["RSI"] > rsi_upper)
        | (data["RSI"] < rsi_lower)
    )

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

    final_balance = balance + (shares_held * data.iloc[-1]["Close"])
    return final_balance - INITIAL_BALANCE, trade_log, final_balance


# Step 4: Optimize Parameters via Grid Search
results = []
for (ema_short, ema_long), (rsi_lower, rsi_upper) in product(
    EMA_WINDOWS, RSI_THRESHOLDS
):
    if ema_short >= ema_long:
        continue
    profit, _, _ = backtest_scalping(
        data.copy(), ema_short, ema_long, rsi_lower, rsi_upper
    )
    results.append(
        {
            "EMA_Short": ema_short,
            "EMA_Long": ema_long,
            "RSI_Lower": rsi_lower,
            "RSI_Upper": rsi_upper,
            "Profit": profit,
        }
    )

# Step 5: Analyze Optimization Results
results_df = pd.DataFrame(results)
best_params = results_df.loc[results_df["Profit"].idxmax()]
print("\n--- Best Parameters ---")
print(best_params)

# Step 6: Apply Best Parameters and Re-run Scalping
profit, trade_log, final_balance = backtest_scalping(
    data,
    int(best_params["EMA_Short"]),
    int(best_params["EMA_Long"]),
    best_params["RSI_Lower"],
    best_params["RSI_Upper"],
)

# Step 7: Print Trade Log
print("\n--- Trade Log ---")
for trade in trade_log:
    print(
        f"{trade[0]}: {trade[1]} {trade[2]} shares at ${trade[3]:.2f}, Balance: ${trade[4]:.2f}"
    )

# Step 8: Final Balance and Net Profit
print(f"\nFinal Balance: ${final_balance:.2f}")
print(f"Net Profit: ${profit:.2f}")

# Step 9: Plot Results with Optimized Parameters
data["EMA_Short"] = EMAIndicator(
    data["Close"], window=int(best_params["EMA_Short"])
).ema_indicator()
data["EMA_Long"] = EMAIndicator(
    data["Close"], window=int(best_params["EMA_Long"])
).ema_indicator()
plt.figure(figsize=(14, 8))
plt.plot(data.index, data["Close"], label="Close Price", color="blue")
plt.plot(
    data.index,
    data["EMA_Short"],
    label=f"EMA{int(best_params['EMA_Short'])}",
    color="green",
)
plt.plot(
    data.index,
    data["EMA_Long"],
    label=f"EMA{int(best_params['EMA_Long'])}",
    color="red",
)

# Plot Buy/Sell Signals
buy_signals = data[data["Buy_Signal"]]
sell_signals = data[data["Sell_Signal"]]
plt.scatter(
    buy_signals.index,
    buy_signals["Close"],
    label="Buy Signal",
    marker="^",
    color="green",
)
plt.scatter(
    sell_signals.index,
    sell_signals["Close"],
    label="Sell Signal",
    marker="v",
    color="red",
)

plt.title("Optimized Scalping Strategy")
plt.xlabel("Date")
plt.ylabel("Price")
plt.legend()
plt.grid()
plt.show()
