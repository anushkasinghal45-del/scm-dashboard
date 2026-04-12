import pandas as pd
import numpy as np

sales = pd.read_csv("sales_final.csv")

# assign random warehouse_id (1–5)
np.random.seed(42)
sales["warehouse_id"] = np.random.randint(1, 6, size=len(sales))

# save updated file
sales.to_csv("sales_final.csv", index=False)

print("sales_final.csv updated with warehouse_id")
