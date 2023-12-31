import time
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate
import json

import pandas as pd

DELTA = 1e-3

plt.rcParams["date.autoformatter.day"] = "%m-%d"
EnergyHistory_data = pd.read_csv("../data/EnergyHistory.csv")

plt.plot(EnergyHistory_data["DateTime"], EnergyHistory_data["Consume"], linewidth=7, label="No Unforeseen Circumstances")
EnergyHistory_data.loc[(408, "Consume")] = 500
EnergyHistory_data.loc[(483, "Consume")] = 300
EnergyHistory_data.loc[(484, "Consume")] = 300
EnergyHistory_data.loc[(485, "Consume")] = 300
EnergyHistory_data.loc[(486, "Consume")] = 300

EnergyHistory_data.loc[(201, "Consume")] = 0
EnergyHistory_data.loc[(199, "Consume")] = 0
EnergyHistory_data.loc[(200, "Consume")] = 0
# EnergyHistory_data = EnergyHistory_data.iloc[400:500]

data = plt.plot(EnergyHistory_data["DateTime"], EnergyHistory_data["Consume"], linewidth=3, label="With Unforeseen Circumstance")
data[0].axes.get_xaxis().set_visible(False)
plt.legend(loc="upper right")
plt.savefig("./figure/unforeseen_circumstances.png", dpi=300)
plt.show()

# EnergyHistory_data.loc[(168, "Consume")] = 500
# EnergyHistory_data.loc[(408, "Consume")] = 500
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


# print(tabulate(SunlightHistory_data, headers='keys', tablefmt='psql'))


class System:
    def __init__(self, solar: int, battery: int):
        self.result = []
        self.purchase_by_time = [0] * 24

        global EnergyHistory_data, SunlightHistory_data
        self.solar_size = solar
        self.solar_cost = self.solar_size * (500 / 10 / 12)
        self.battery_number = battery
        self.battery_unit_capacity = 10.5 * 0.9
        self.convert_cost = 500 * 3 / 5 / 12
        self.cost_effi = 0.95
        self.max_battery = self.battery_number * self.battery_unit_capacity
        self.battery_cost = ((2 * self.max_battery + 1200) / 10 / 12)
        if self.max_battery > 1500:
            assert False, "Battery size exceeds limit!"
        self.current_battery = self.max_battery
        self.electricity_cost = 0
        self.electricity_purchased = 0
        self.wasted = 0

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
        assert datetime.strptime(EnergyHistory_data.iloc[self.step]["DateTime"], "%m/%d/%Y %H:%M") == self.time
        if not 0 - DELTA <= battery_charge + self.current_battery <= self.max_battery + DELTA:
            assert False, f"Battery amount invalid!, charge {battery_charge} to {battery_charge + self.current_battery}!"
        solar = SunlightHistory_data.iloc[self.step]["Electricity"]  # 单位面积太阳能发电量
        energy = EnergyHistory_data.iloc[self.step]["Consume"]  # 用电量
        if solar * self.solar_size * self.cost_effi + DELTA < battery_charge:
            assert False, f"Not enough solar power for charging!"

        if battery_charge > 0:
            bi = battery_charge
            bo = 0
            pv = solar * self.solar_size - bi / self.cost_effi
        else:
            bi = 0
            bo = -battery_charge
            pv = solar * self.solar_size
        if pv > energy / self.cost_effi:
            self.wasted += pv - energy / self.cost_effi
        pv = min(pv, energy / self.cost_effi)
        # Here waste any more power
        pg = (energy - pv * self.cost_effi - bo * self.cost_effi * self.cost_effi) / self.cost_effi
        # pg = energy / self.cost_effi - pv - bo * self.cost_effi
        assert pg + DELTA >= 0
        self.electricity_cost += calculate_electricity_price(self.time) * pg
        self.electricity_purchased += pg
        self.purchase_by_time[self.time.hour] += pg
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
            val["energy_pv"] = float(round(val["energy_pv"], 4))
            val["energy_bi"] = float(round(val["energy_bi"], 4))
            val["energy_bo"] = float(round(val["energy_bo"], 4))
            val["energy_pg"] = float(round(val["energy_pg"], 4))

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
        return self.electricity_cost, self.electricity_purchased, self.purchase_by_time


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
        if 0 <= data["time"].hour <= 4:
            sy.update(0)
            continue
        if data["solar"] * sy.cost_effi > data["consume"]:
            sy.update((min((data["solar"] * sy.cost_effi - data["consume"]), sy.max_battery - data["battery"])))
        else:
            sy.update(-min((data["consume"] - data["solar"] * sy.cost_effi) / sy.cost_effi / sy.cost_effi, data["battery"]))


def no_op(sy: System):
    for i in range(24 * 31):
        sy.update(0)


# # total_purchased = 0
# s = System(2000, 120)
# with open("../sample.json", "r") as file:
#     file = json.load(file)
#     file = file["system_result"]
#     for i in file:
#         s.update(i["energy_bi"] - i["energy_bo"])
#         # total_purchased += i["energy_pg"]
# # print(total_purchased)
#
# with open("../sample.json", "r") as file:
#     file = json.load(file)
#     file = file["system_result"]
#     line = 0
#     for i in file:
#         assert abs(i["energy_bo"] - s.result[line]["energy_bo"]) < DELTA
#         assert abs(i["energy_bi"] - s.result[line]["energy_bi"]) < DELTA
#         assert abs(i["energy_pg"] - s.result[line]["energy_pg"]) < DELTA
#         line += 1

# with open("../data/Examples.csv", "r") as file:
#     for i in file:
#         if 'date_time' in i:
#             continue
#         i = i.strip("\n").split(",")
#         bo = float(i[6])
#         bi = float(i[5])
#         s.update(bi - bo)

# print(round(s.get_result(), 4), sep=",")
# print(s.get_purchase())
# with open("./part1.json", "w") as f:
#     f.write(s.get_json())
# exit(0)

# s = System(1500, 150)
# sb_stra(s)
# print(round(s.get_result(), 4), s.get_purchase())
#

s = System(2861, 158)
sb_stra(s)
print(round(s.get_result(), 4), s.get_purchase())
# with open("./part1.json", "w") as f:
#     print(s.get_result())
#     f.write(s.get_json())
# print(s.wasted)
# print(s.get_purchase()[2])

# init_time = datetime(2023, 5, 1, 0)
# pg_5_6_7 = [0] * 31
# for i in s.result:
#     if 5 <= init_time.hour < 8:
#         pg_5_6_7[init_time.day - 1] += i["energy_pg"]
#     init_time += timedelta(hours=1)
# print(pg_5_6_7)
# plt.plot(range(1, 32), pg_5_6_7)
# plt.show()

# for i in range(158, 159, 5):
#     for j in range(2850, 2926, 1):
#         s = System(j, i)
#         sb_stra(s)
#         print(j, i, round(s.get_result(), 4), sep=",")
