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
plt.clf()


def light_gen_electricity(rad, temp):
    P_STC = 250
    G_AC = rad
    G_STC = 1000
    T_E = temp
    T_C = T_E + 30 * G_AC / 1000
    T_R = 25
    delta = -0.47 * 0.01
    P_p_t = P_STC * G_AC * (1 + delta * (T_C - T_R)) / G_STC
    return P_p_t


SunlightHistory_data = pd.read_csv("./data/SunlightHistory.csv")
print(SunlightHistory_data)
SunlightHistory_data["elec"] = light_gen_electricity(SunlightHistory_data["Radiation"], SunlightHistory_data["Temperature"])
plt.plot(SunlightHistory_data["DateTime"].values, SunlightHistory_data["elec"].values)
plt.title("DateTime-Sunlight")
plt.savefig("./vis/DateTime-Sunlight")
plt.clf()
