import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# Load products to get price
products = pd.read_csv("products_final.csv")

data = []
start_date = datetime(2023, 1, 1)

for i in range(500):
    product_id = np.random.randint(1, 21)
    quantity = np.random.randint(5, 50)
    
    # get product price
    price = products.loc[products["product_id"] == product_id, "price"].values[0]
    
    revenue = quantity * price

    data.append({
        "sale_id": i+1,
        "product_id": product_id,
        "quantity_sold": quantity,
        "sale_date": start_date + timedelta(days=i),
        "warehouse_id": np.random.randint(1, 6),
        "revenue": revenue
    })

sales = pd.DataFrame(data)
sales.to_csv("sales_final.csv", index=False)

print("sales_final.csv recreated with revenue")
