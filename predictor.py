def predict_price(rows):
    """Predict next price based on trend analysis of historical data."""
    if not rows or len(rows) == 0:
        return "Not enough data for prediction"
    
    try:
        # Extract prices
        prices = [float(row[1]) for row in rows]
        
        if len(prices) < 2:
            return f"Current average price: ${sum(prices) / len(prices):.2f}"
        
        # Calculate simple moving average trend
        recent_prices = prices[-5:] if len(prices) >= 5 else prices
        avg_price = sum(recent_prices) / len(recent_prices)
        
        # Calculate trend (simple: compare last vs previous)
        if len(prices) >= 2:
            trend = prices[-1] - prices[-2]
            predicted_price = prices[-1] + (trend * 0.5)  # Assume 50% of recent trend continues
        else:
            predicted_price = avg_price
        
        return f"Predicted next price: ${predicted_price:.2f} (Current: ${prices[-1]:.2f})"
    except Exception as e:
        print(f"Prediction error: {e}")
        return "Error calculating prediction"
