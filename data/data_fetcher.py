import requests
import pandas as pd
import websocket
import json
from threading import Thread
import time

# Step 1: Define Polygon API Key
API_KEY = (
    "kNC1GSQ9nayON7oiIxts48lDBPp357Mj"  # Replace with your actual Polygon.io API key
)


# Step 2: Fetch Historical Data
def fetch_polygon_historical_data(ticker, multiplier, timespan, from_date, to_date):
    """
    Fetch historical candlestick data from Polygon.io.
    """
    print(f"Fetching historical data for {ticker} from {from_date} to {to_date}...")

    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
    params = {"apiKey": API_KEY}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if "results" in data and data["results"]:
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
            print("Historical data fetched successfully.")
            return df[["Open", "High", "Low", "Close", "Volume"]]
        else:
            raise ValueError("No data found in the response.")
    else:
        raise ValueError(
            f"Error fetching data: {response.status_code}, {response.text}"
        )


# Step 3: Fetch Real-Time Data
def fetch_polygon_real_time_data(ticker):
    """
    Fetch real-time trade data using Polygon.io WebSocket API.
    """
    ws_url = f"wss://socket.polygon.io/stocks"
    print(f"Connecting to Polygon WebSocket for real-time data: {ticker}")

    def on_message(ws, message):
        """
        Callback for handling incoming WebSocket messages.
        """
        data = json.loads(message)
        if data and data[0]["ev"] == "T":  # 'T' is the event type for trade updates
            trade_data = data[0]
            timestamp = pd.to_datetime(
                trade_data["t"], unit="ms"
            )  # Convert UNIX time to datetime
            price = trade_data["p"]
            size = trade_data["s"]
            print(f"Real-time update: {timestamp} - Price: {price}, Size: {size}")

    def on_error(ws, error):
        print(f"WebSocket error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print("WebSocket connection closed.")

    def on_open(ws):
        """
        Subscribe to real-time data for the specified ticker.
        """
        print(f"Subscribing to real-time data for {ticker}...")
        auth_message = {"action": "auth", "params": API_KEY}
        ws.send(json.dumps(auth_message))
        subscribe_message = {"action": "subscribe", "params": f"T.{ticker}"}
        ws.send(json.dumps(subscribe_message))

    # Start WebSocket connection
    ws = websocket.WebSocketApp(
        ws_url, on_message=on_message, on_error=on_error, on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever()


# Step 4: Run Historical and Real-Time Fetching
if __name__ == "__main__":
    # Historical Data Fetch
    TICKER = "TSLA"
    FROM_DATE = "2024-12-20"  # Start date (YYYY-MM-DD)
    TO_DATE = "2024-12-27"  # End date (YYYY-MM-DD)
    historical_data = fetch_polygon_historical_data(
        ticker=TICKER,
        multiplier=1,  # 1-minute intervals
        timespan="minute",  # Fetch minute-level data
        from_date=FROM_DATE,
        to_date=TO_DATE,
    )

    # Display Historical Data
    print("\n--- Historical Data ---")
    print(historical_data.head())

    # Real-Time Data Fetch
    real_time_thread = Thread(target=fetch_polygon_real_time_data, args=(TICKER,))
    real_time_thread.start()

    # Keep Main Program Running
    while True:
        time.sleep(2)
