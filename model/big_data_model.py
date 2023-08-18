import time
from datetime import datetime, timedelta

import pandas as pd

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
