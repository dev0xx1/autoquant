price_lookback_window_days = 7
predictor_model = "gemini/gemini-2.5-flash"
temperature = 0.2

prompt = """
You are a financial market predictor. Given recent price data and news, predict whether the stock price will go UP or DOWN in the next 24 hours.

Analyze the price trend, volume patterns, and news sentiment to make your prediction.
Respond with exactly UP or DOWN.
"""


def process_prices(price_rows):
    if not price_rows:
        return {}
    prices = [float(r["price"]) for r in price_rows]
    volumes = [float(r["volume"]) for r in price_rows]
    return {
        "current_price": prices[-1],
        "price_change_pct": (prices[-1] - prices[0]) / prices[0] * 100 if prices[0] else 0,
        "avg_volume": sum(volumes) / len(volumes) if volumes else 0,
        "price_min": min(prices),
        "price_max": max(prices),
    }
