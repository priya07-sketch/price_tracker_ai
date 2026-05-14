from flask import Flask, render_template, request, redirect, url_for
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import os
import urllib.parse

from scraper import get_price
from database import create_db, insert_price, get_prices, get_all_products, get_latest_price
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
                message=str(e)
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
        # Show helpful message with available products
        all_products = get_all_products()
        error_msg = f"❌ No data found for '{product}'."
        if all_products:
            error_msg += f" Available products: {', '.join(all_products[:5])}"
            if len(all_products) > 5:
                error_msg += f" and {len(all_products)-5} more."
        else:
            error_msg += " Try scraping a product URL first!"
        
        return render_template("dashboard.html",
                               product=product,
                               prediction=error_msg,
                               graph=None,
                               latest_price=None)

    df=pd.DataFrame(rows,columns=["date","price"])

    df["date"]=pd.to_datetime(df["date"])

    plt.figure(figsize=(10, 6))
    
    plt.plot(df["date"],df["price"],marker='o', linewidth=2, markersize=6)

    plt.xlabel("Date", fontsize=12)

    plt.ylabel("Price (₹)", fontsize=12)

    plt.title(f"Price Trend - {product}", fontsize=14, fontweight='bold')
    
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("static/graph.png", dpi=100)
    plt.close()

    prediction=predict_price(rows)
    
    latest_price = get_latest_price(product)

    return render_template("dashboard.html",
                           product=product,
                           prediction=prediction,
                           graph="static/graph.png",
                           latest_price=latest_price)


@app.route("/products", methods=["GET"])
def products():
    """Show all products in the database."""
    all_products = get_all_products()
    product_data = []
    
    for product in all_products:
        rows = get_prices(product)
        latest_price = get_latest_price(product)
        product_data.append({
            'name': product,
            'price': latest_price,
            'records': len(rows)
        })
    
    return render_template("products.html", products=product_data)

    

if __name__=="__main__":
    # Running with debug=False suppresses the development-server warning message
    # (in production, you should use a proper WSGI server instead).
    app.run(debug=False)