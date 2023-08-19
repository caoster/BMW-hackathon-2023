import time
from datetime import datetime, timedelta

import pandas as pd
import matplotlib.pyplot as plt

DELTA = 1e-3

EnergyHistory_data = pd.read_csv("../data/EnergyHistory.csv")
Table = pd.read_csv("../data/SunlightHistory.csv")
Table["Consume"] = EnergyHistory_data["Consume"]
del EnergyHistory_data


def light_gen_electricity(rad, temp):
    P_STC = 250
    G_AC = rad
    G_STC = 1000
    T_E = temp
    T_C = T_E + 30 * G_AC / 1000
    T_R = 25
    delta = -0.47 * 0.01
    P_p_t = P_STC * G_AC * (1 + delta * (T_C - T_R)) / G_STC
    return P_p_t / 1000


def calculate_electricity_price(time: datetime):
    if 8 <= time.hour < 12 or 17 <= time.hour < 21:
        return 0.628
    elif 5 <= time.hour < 8 or 12 <= time.hour < 17 or 21 <= time.hour < 22:
        return 0.529
    else:
        return 0.450


Table["UnitSolar"] = light_gen_electricity(Table["Radiation"], Table["Temperature"])
del Table["Radiation"], Table["Temperature"]
Table["DateTime"] = pd.to_datetime(Table["DateTime"], format="%m/%d/%Y %H:%M")
Table["PriceUnit"] = Table["DateTime"].apply(calculate_electricity_price)

# Table.plot(x="DateTime", y=["Consume", "UnitSolar", "PriceUnit"], legend=True)
# plt.plot(Table["DateTime"], Table["UnitSolar"], label="UnitSolar")
# plt.savefig("UnitSolar.png")
# plt.show()

# UnitSolar_combined = [0] * 24
# for i in range(len(Table)):
#     UnitSolar_combined[Table.iloc[i]["DateTime"].hour] += Table.iloc[i]["UnitSolar"]
#
# plt.plot(range(1, 25), UnitSolar_combined, label="UnitSolar")
# plt.savefig("UnitSolar.png")
# plt.show()

for i in range(31):
    plt.plot(range(1, 25), Table["UnitSolar"].iloc[(24 * i):(24 * i + 24)], label=f"Week{i + 1}")
plt.savefig("UnitSolar.png", dpi=1000)
