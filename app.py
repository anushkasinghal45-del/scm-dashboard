import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="SCM Dashboard", layout="wide")
st.title("📦 Centralized Supply Chain Monitoring System")

# ----------------------------
# LOAD DATA
# ----------------------------
products = pd.read_csv("products_final.csv")
inventory = pd.read_csv("inventory_final.csv")
sales = pd.read_csv("sales_final.csv")
orders = pd.read_csv("orders_final.csv")
warehouses = pd.read_csv("warehouses_final.csv")

# ----------------------------
# MERGE DATA
# ----------------------------
inventory = inventory.merge(products, on="product_id")
inventory = inventory.merge(warehouses, on="warehouse_id")

sales = sales.merge(products, on="product_id")
sales = sales.merge(warehouses, on="warehouse_id")

# 🔥 FIX: add product_name to orders
orders = orders.merge(products, on="product_id")

# ----------------------------
# SIDEBAR FILTERS
# ----------------------------
st.sidebar.header("Filters")

selected_product = st.sidebar.selectbox(
    "Select Product",
    ["All"] + list(products["product_name"].unique())
)

selected_warehouse = st.sidebar.selectbox(
    "Select Warehouse",
    ["All"] + list(warehouses["location"].unique())
)

# ----------------------------
# APPLY FILTERS
# ----------------------------
filtered_inventory = inventory.copy()
filtered_sales = sales.copy()

if selected_product != "All":
    filtered_inventory = filtered_inventory[
        filtered_inventory["product_name"] == selected_product
    ]
    filtered_sales = filtered_sales[
        filtered_sales["product_name"] == selected_product
    ]

if selected_warehouse != "All":
    filtered_inventory = filtered_inventory[
        filtered_inventory["location"] == selected_warehouse
    ]
    filtered_sales = filtered_sales[
        filtered_sales["location"] == selected_warehouse
    ]

# ----------------------------
# KPIs (GLOBAL)
# ----------------------------
total_inventory = int(inventory["stock_level"].sum())

stockouts = int(
    (inventory["stock_level"] <= inventory["reorder_level"]).sum()
)

excess = int(
    (inventory["stock_level"] > inventory["reorder_level"] * 2).sum()
)

# safer revenue calculation
if "revenue" in sales.columns:
    total_revenue = int(sales["revenue"].sum())
else:
    total_revenue = int(sales["quantity_sold"].sum())

total_orders = len(orders)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Inventory", total_inventory)
col2.metric("Stockouts 🔴", stockouts)
col3.metric("Excess 🟠", excess)
col4.metric("Revenue 🟢", total_revenue)
col5.metric("Orders", total_orders)

# ----------------------------
# DEMAND TREND
# ----------------------------
st.subheader("📈 Demand Trend")

filtered_sales["sale_date"] = pd.to_datetime(filtered_sales["sale_date"])

trend = filtered_sales.groupby("sale_date")["quantity_sold"].sum().reset_index()

fig_trend = px.line(trend, x="sale_date", y="quantity_sold")
st.plotly_chart(fig_trend, use_container_width=True)

# ----------------------------
# DEMAND FORECAST (ML)
# ----------------------------
st.subheader("🔮 Demand Forecast")

if len(filtered_sales) > 0:

    filtered_sales["days"] = (
        filtered_sales["sale_date"] - filtered_sales["sale_date"].min()
    ).dt.days

    daily_sales = filtered_sales.groupby("days")["quantity_sold"].sum().reset_index()

    if len(daily_sales) > 2:

        X = daily_sales[["days"]]
        y = daily_sales["quantity_sold"]

        poly = PolynomialFeatures(degree=3)
        X_poly = poly.fit_transform(X)

        model = LinearRegression()
        model.fit(X_poly, y)

        future_days = np.arange(
            daily_sales["days"].max() + 1,
            daily_sales["days"].max() + 31
        ).reshape(-1, 1)

        future_poly = poly.transform(future_days)
        predictions = model.predict(future_poly)

        # add variation
        noise = np.random.normal(0, 1.5, len(predictions))
        seasonality = 3 * np.sin(np.linspace(0, 3, len(predictions))

)
        predictions = predictions + noise + seasonality

        forecast_df = pd.DataFrame({
            "day": future_days.flatten(),
            "predicted_sales": predictions
        })

        fig_forecast = px.line(
            forecast_df,
            x="day",
            y="predicted_sales"
        )

        st.plotly_chart(fig_forecast, use_container_width=True)

    else:
        st.warning("Not enough data for forecasting")

# ----------------------------
# INVENTORY BY WAREHOUSE
# ----------------------------
st.subheader("🏭 Inventory by Warehouse")

inv_group = filtered_inventory.groupby("location")["stock_level"].sum().reset_index()

fig_inv = px.bar(inv_group, x="location", y="stock_level")
st.plotly_chart(fig_inv, use_container_width=True)

# ----------------------------
# ORDER STATUS
# ----------------------------
st.subheader("📦 Order Status Distribution")

order_status = orders["status"].value_counts().reset_index()
order_status.columns = ["status", "count"]

fig_orders = px.pie(order_status, names="status", values="count")
st.plotly_chart(fig_orders, use_container_width=True)

# ----------------------------
# ALERT TABLES
# ----------------------------
st.subheader("🚨 Critical Stock Alerts")

critical = filtered_inventory[
    filtered_inventory["stock_level"] <= filtered_inventory["reorder_level"]
]

st.dataframe(critical[
    ["product_name", "location", "stock_level", "reorder_level"]
])

st.subheader("📊 Overstocked Items")

overstock = filtered_inventory[
    filtered_inventory["stock_level"] > filtered_inventory["reorder_level"] * 2
]

st.dataframe(overstock[
    ["product_name", "location", "stock_level", "reorder_level"]
])

st.subheader("⏳ Delayed Orders")

delayed = orders[orders["status"] == "Delayed"]

st.dataframe(delayed[
    ["product_name", "order_date", "delivery_date", "status"]
])
