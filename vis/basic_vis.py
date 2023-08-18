import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

EnergyHistory_data = pd.read_csv("./data/EnergyHistory.csv")
print(EnergyHistory_data)

print(EnergyHistory_data["Consume"].mean())

# plt.plot(EnergyHistory_data["DateTime"].values, EnergyHistory_data["Consume"].values)
# plot datetime and value

plt.plot(EnergyHistory_data["DateTime"].values, EnergyHistory_data["Consume"].values)
plt.title("DateTime-Consume")
plt.savefig("./vis/DateTime-Consume")
