import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="SCM Dashboard", layout="wide")

# ----------------------------
# SOFT BACKGROUND (FIXED)
# ----------------------------
st.set_page_config(page_title="SCM Dashboard", layout="wide")

st.markdown(
    """
    <style>
    body {
        background-color: #0e1117;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📦 Centralized Supply Chain Monitoring System")

# ----------------------------
# LOAD DATA
# ----------------------------
products = pd.read_csv("products_final.csv")
inventory = pd.read_csv("inventory_final.csv")
sales = pd.read_csv("sales_final.csv")
orders = pd.read_csv("orders_final.csv")
warehouses = pd.read_csv("warehouses_final.csv")

# Forecast safe load
if os.path.exists("forecast.csv"):
    forecast = pd.read_csv("forecast.csv")
else:
    forecast = pd.DataFrame({"day": [], "predicted_sales": []})

# ----------------------------
# MERGE
# ----------------------------
inventory = inventory.merge(products, on="product_id")
inventory = inventory.merge(warehouses, on="warehouse_id")

sales = sales.merge(products, on="product_id")
sales = sales.merge(warehouses, on="warehouse_id")
orders = orders.merge(products, on="product_id")

# ----------------------------
# SIDEBAR FILTERS
# ----------------------------
st.sidebar.header("Filters")

product_filter = st.sidebar.selectbox(
    "Select Product",
    ["All"] + list(products["product_name"].unique())
)

warehouse_filter = st.sidebar.selectbox(
    "Select Warehouse",
    ["All"] + list(warehouses["location"].unique())
)

# Apply filters
if product_filter != "All":
    inventory = inventory[inventory["product_name"] == product_filter]
    sales = sales[sales["product_name"] == product_filter]
    orders = orders[orders["product_name"] == product_filter]

if warehouse_filter != "All":
    inventory = inventory[inventory["location"] == warehouse_filter]
    sales = sales[sales["location"] == warehouse_filter]

# ----------------------------
# KPI CALCULATIONS
# ----------------------------
inventory["Stockout"] = inventory["stock_level"] < inventory["reorder_level"]
inventory["Excess"] = inventory["stock_level"] > inventory["reorder_level"] + 100

total_inventory = int(inventory["stock_level"].sum())
stockouts = int(inventory["Stockout"].sum())
excess = int(inventory["Excess"].sum())
total_revenue = int(sales["revenue"].sum())
total_orders = len(orders)

# ----------------------------
# KPI DISPLAY
# ----------------------------
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Inventory", total_inventory)
col2.metric("Stockouts 🔴", stockouts)
col3.metric("Excess 🟠", excess)
col4.metric("Revenue 🟢", total_revenue)
col5.metric("Orders", total_orders)

# ----------------------------
# DEMAND TREND
# ----------------------------
sales["sale_date"] = pd.to_datetime(sales["sale_date"])
trend = sales.groupby("sale_date")["quantity_sold"].sum().reset_index()

fig_trend = px.line(trend, x="sale_date", y="quantity_sold")

# ----------------------------
# FORECAST
# ----------------------------
if not forecast.empty:
    fig_forecast = px.line(forecast, x="day", y="predicted_sales")

# ----------------------------
# ROW 1 (Trend + Forecast)
# ----------------------------
colA, colB = st.columns(2)

with colA:
    st.subheader("📈 Demand Trend")
    st.plotly_chart(fig_trend, use_container_width=True)

with colB:
    st.subheader("🔮 Forecast")
    if not forecast.empty:
        st.plotly_chart(fig_forecast, use_container_width=True)
    else:
        st.info("Forecast not available")

# ----------------------------
# INVENTORY
# ----------------------------
inv_group = inventory.groupby("location")["stock_level"].sum().reset_index()
fig_inv = px.bar(inv_group, x="location", y="stock_level")

# ----------------------------
# ORDER STATUS
# ----------------------------
order_status = orders["status"].value_counts().reset_index()
order_status.columns = ["status", "count"]
fig_orders = px.pie(order_status, names="status", values="count")

# ----------------------------
# ROW 2 (Inventory + Orders)
# ----------------------------
colC, colD = st.columns(2)

with colC:
    st.subheader("🏭 Inventory by Warehouse")
    st.plotly_chart(fig_inv, use_container_width=True)

with colD:
    st.subheader("📦 Order Status")
    st.plotly_chart(fig_orders, use_container_width=True)

# ----------------------------
# ALERT TABLES
# ----------------------------
st.subheader("🚨 Critical Stock Alerts")
st.dataframe(inventory[inventory["Stockout"]][
    ["product_name", "location", "stock_level", "reorder_level"]
])

st.subheader("📊 Overstocked Items")
st.dataframe(inventory[inventory["Excess"]][
    ["product_name", "location", "stock_level", "reorder_level"]
])

st.subheader("⏳ Delayed Orders")
st.dataframe(orders[orders["status"] == "Delayed"][
    ["product_name", "order_date", "delivery_date", "status"]
])
