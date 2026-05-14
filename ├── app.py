from flask import Flask, render_template, request, redirect, url_for
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import os
import urllib.parse

from scraper import get_price
from database import create_db, insert_price, get_prices
from predictor import predict_price

app = Flask(__name__)

# Create static directory if it doesn't exist
if not os.path.exists('static'):
    os.makedirs('static')

create_db()

@app.route("/", methods=["GET","POST"])
def index():

    message=None

    if request.method=="POST":

        url=request.form["url"].strip()

        # Validate URL format
        if not url:
            message="❌ Please enter a URL."
        else:
            try:
                # If URL doesn't have a scheme, assume https
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                # Validate URL structure
                parsed = urllib.parse.urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    message="❌ Invalid URL format. Please enter a valid URL (e.g., amazon.com/dp/B123456)."
                else:
                    product, price = get_price(url)

                    if price:

                        date=str(datetime.date.today())

                        insert_price(product,price,date)

                        message="✓ Price saved successfully!"
                        
                        # Redirect to dashboard to show graph automatically
                        return redirect(url_for('dashboard', product=product))
                    else:
                        message="❌ Could not find price on this page. The website may not be supported or lacks pricing information."
            except ValueError as e:
                message=f"❌ {str(e)}"
            except TimeoutError as e:
                message=f"❌ {str(e)}"
            except PermissionError as e:
                message=f"❌ {str(e)}"
            except ConnectionError as e:
                message=f"❌ {str(e)}"
            except Exception as e:
                message=f"❌ Error: {str(e)}"

    return render_template("index.html",message=message)


@app.route("/dashboard", methods=["GET","POST"])
def dashboard():

    if request.method == "POST":
        product=request.form["product"]
    else:
        product=request.args.get("product")
    
    if not product:
        return redirect(url_for('index'))
    
    rows=get_prices(product)
    
    if not rows:
        return f"<h2>No data found for {product}</h2><a href='/'>Back</a>"

    df=pd.DataFrame(rows,columns=["date","price"])

    df["date"]=pd.to_datetime(df["date"])

    plt.figure()

    plt.plot(df["date"],df["price"],marker='o')

    plt.xlabel("Date")

    plt.ylabel("Price")

    plt.title(product)
    plt.tight_layout()
    plt.savefig("static/graph.png")
    plt.close()

    prediction=predict_price(rows)

    return render_template("dashboard.html",
                           product=product,
                           prediction=prediction,
                           graph="static/graph.png")
    

if __name__=="__main__":
    app.run(debug=True)