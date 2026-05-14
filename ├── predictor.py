import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def predict_price(data):

    df = pd.DataFrame(data, columns=["date","price"])

    df["day"] = range(len(df))

    X = df[["day"]]
    y = df["price"]

    model = LinearRegression()

    model.fit(X, y)

    future_day = np.array([[len(df)+1]])

    prediction = model.predict(future_day)

    return round(prediction[0],2)
