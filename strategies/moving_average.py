def moving_average_crossover(data, short_window=50, long_window=200):
    """
    Moving Average Crossover Strategy.
    """
    data["SMA_Short"] = data["Close"].rolling(window=short_window).mean()
    data["SMA_Long"] = data["Close"].rolling(window=long_window).mean()
    data["Signal"] = 0

    # Generate signals
    data.loc[data["SMA_Short"] > data["SMA_Long"], "Signal"] = 1
    data.loc[data["SMA_Short"] <= data["SMA_Long"], "Signal"] = -1
    return data
