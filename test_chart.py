import customtkinter as ctk
import mplfinance as mpf
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta

# Sample data
data = []
for i in range(10):
    data.append({
        'Date': datetime.now() - timedelta(days=i),
        'Open': 0,
        'High': 500,
        'Low': -200,
        'Close': 300
    })

df = pd.DataFrame(data)
df.set_index('Date', inplace=True)
df.sort_index(inplace=True)

root = ctk.CTk()
root.geometry("800x600")

fig, ax = mpf.plot(df, type='candle', returnfig=True, figsize=(8, 6))

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack(fill="both", expand=True)

root.mainloop()