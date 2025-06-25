import pandas as pd
from tensorboardX import SummaryWriter

# Load your real expense data here
df = pd.read_csv("your_expense_data.csv")  # Replace with actual path
df['date'] = pd.to_datetime(df['date'])

# Total and category breakdown
total = df['amount'].sum()
by_category = df.groupby("category")['amount'].sum()
percentages = by_category / total * 100

# Write to TensorBoard
writer = SummaryWriter(logdir="logs/")
writer.add_scalar("Budget/Total_Expense", total, 0)
for cat in ['Need', 'Want', 'Saving']:
    writer.add_scalar(f"Budget/{cat}_Amount", by_category.get(cat, 0.0), 0)
    writer.add_scalar(f"Budget/{cat}_Percentage", percentages.get(cat, 0.0), 0)
writer.close()
