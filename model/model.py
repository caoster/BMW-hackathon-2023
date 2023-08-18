import time
from datetime import datetime, timedelta
from tabulate import tabulate
import json

import pandas as pd

DELTA = 1e-3

EnergyHistory_data = pd.read_csv("../data/EnergyHistory.csv")
SunlightHistory_data = pd.read_csv("../data/SunlightHistory.csv")


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


SunlightHistory_data["Electricity"] = light_gen_electricity(SunlightHistory_data["Radiation"], SunlightHistory_data["Temperature"])


# print(tabulate(SunlightHistory_data, headers = 'keys', tablefmt = 'psql'))

class System:
    def __init__(self, solar: int, battery: int):
        self.result = []

        global EnergyHistory_data, SunlightHistory_data
        self.solar_size = solar
        self.solar_cost = self.solar_size * (500 / 10 / 12)
        self.battery_number = battery
        self.battery_cost = 2 * self.battery_number + (1200 / 10 / 12)
        self.battery_unit_capacity = 10.5 * 0.9
        self.convert_cost = 500 * 3 / 5 / 12
        self.cost_effi = 0.95
        self.max_battery = self.battery_number * self.battery_unit_capacity
        if self.max_battery > 1500:
            assert False, "Battery size exceeds limit!"
        self.current_battery = self.max_battery
        self.electricity_cost = 0
        self.electricity_purchased = 0

        # These two shall be updated together!
        self.time = datetime(2023, 5, 1, 0)
        self.step = 0

    def _add_result(self, pv, bi, bo, pg):
        self.result.append({
            "energy_pv": pv,
            "energy_bi": bi,
            "energy_bo": bo,
            "energy_pg": pg
        })

    def update(self, battery_charge):
        if not 0 - DELTA <= battery_charge + self.current_battery <= self.max_battery + DELTA:
            assert False, f"Battery amount invalid!, charge {battery_charge} to {battery_charge + self.current_battery}!"
        solar = SunlightHistory_data.iloc[self.step]["Electricity"]
        energy = EnergyHistory_data.iloc[self.step]["Consume"]
        if solar * self.solar_size * self.cost_effi + DELTA < battery_charge:
            assert False, f"Not enough solar power for charging!"

        if battery_charge > 0:
            bi = battery_charge
            bo = 0
        else:
            bi = 0
            bo = -battery_charge
        pv = solar * self.solar_size - battery_charge / self.cost_effi
        pv = min(pv, energy / self.cost_effi)
        # Here waste any more power
        pg = (energy - pv * self.cost_effi) / self.cost_effi
        self.electricity_cost += calculate_electricity_price(self.time) * pg
        self.electricity_purchased += pg
        self.current_battery += battery_charge
        # TODO: update battery cycle

        self._add_result(pv, bi, bo, pg)
        self.time += timedelta(hours=1)
        self.step += 1

    def get_data(self):
        return {
            "time": self.time,
            "battery": self.current_battery,
            "solar": SunlightHistory_data.iloc[self.step]["Electricity"] * self.solar_size,
            "consume": EnergyHistory_data.iloc[self.step]["Consume"]
        }

    def get_result(self):
        return self.electricity_cost + self.convert_cost + self.solar_cost + self.battery_cost

    def get_json(self):
        system_process = []
        for idx, val in enumerate(self.result):
            val["energy_pv"] = round(val["energy_pv"], 4) + 1e-4
            val["energy_bi"] = round(val["energy_bi"], 4) + 1e-4
            val["energy_bo"] = round(val["energy_bo"], 4) + 1e-4
            val["energy_pg"] = round(val["energy_pg"], 4) + 1e-4

            a = SunlightHistory_data.iloc[idx]
            b = EnergyHistory_data.iloc[idx]
            val["date_time"] = a["DateTime"]
            val["radiation"] = a["Radiation"]
            val["temperature"] = a["Temperature"]
            val["consume"] = b["Consume"]
            # TODO: 时间格式
            system_process.append(val)

        return json.dumps({
            "battery_number": self.battery_number,
            "pv_area": self.solar_size,
            "cost": round(self.get_result(), 4),
            "system_result": system_process,
            # "battery_life_consume": 0,
            # "battery_scheduling": [],
        })

    def get_purchase(self):
        return self.electricity_cost, self.electricity_purchased


# cost = 0
# for i in range(24 * 31):
#     v = EnergyHistory_data.iloc[i]
#     d = datetime.strptime(v["DateTime"], "%m/%d/%Y %H:%M")
#     cost += calculate_electricity_price(d) * v["Consume"] / 0.95
# print(cost)
#
# sy = System(0, 0)
# for i in range(24 * 31):
#     # print(sy.get_data())
#     sy.update(0)
# print(sy.get_result())
# sy.get_json()

def sb_stra(sy: System):
    for i in range(24 * 31):
        data = sy.get_data()
        if data["solar"] * sy.cost_effi > data["consume"]:
            sy.update(min((data["solar"] * sy.cost_effi - data["consume"]) * sy.cost_effi, sy.max_battery - data["battery"]))
        else:
            sy.update(-min((data["consume"] - data["solar"] * sy.cost_effi) / sy.cost_effi / sy.cost_effi, data["battery"]))


# s = System(2000, 120)
# with open("../data/Examples.csv", "r") as file:
#     for i in file:
#         if 'date_time' in i:
#             continue
#         i = i.strip("\n").split(",")
#         bo = float(i[6])
#         bi = float(i[5])
#         s.update(bi - bo)
#
# print(round(s.get_result(), 4), sep=",")
# print(s.get_purchase())
# print(s.get_json())
# exit(0)

# s = System(1500, 150)
# sb_stra(s)
# print(round(s.get_result(), 4), s.get_purchase())
#
s = System(3000, 158)
sb_stra(s)
# print(round(s.get_result(), 4), s.get_purchase())
print(s.get_json())

# for i in range(150, 159):
#     for j in range(2500, 4000, 50):
#         s = System(j, i)
#         sb_stra(s)
#         print(j, i, round(s.get_result(), 4), sep=",")
