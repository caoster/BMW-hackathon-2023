import json
import time
from datetime import datetime, timedelta

import pandas as pd
import matplotlib.pyplot as plt

DELTA = 1e-3

Table = None


def init_table():
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
    Table["DateTime"] = pd.to_datetime(Table["DateTime"], format="%m/%d/%Y %H:%M")
    Table["PriceUnit"] = Table["DateTime"].apply(calculate_electricity_price)

    Table["energy_pv"] = 0.0
    Table["energy_bi"] = 0.0
    Table["energy_bo"] = 0.0
    Table["energy_pg"] = 0.0
    Table["battery_after"] = 0.0
    Table["waste_solar"] = 0.0

    return Table


class System:
    def __init__(self, solar: int, battery: int):
        global Table
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

        # These two shall be updated together!
        self.step = 0

    def _add_result(self, pv, bi, bo, pg, waste_solar):
        Table.loc[self.step, "energy_pv"] = pv
        Table.loc[self.step, "energy_bi"] = bi
        Table.loc[self.step, "energy_bo"] = bo
        Table.loc[self.step, "energy_pg"] = pg
        Table.loc[self.step, "battery_after"] = self.current_battery
        Table.loc[self.step, "waste_solar"] = waste_solar

    def update(self, battery_charge):
        if not 0 - DELTA <= battery_charge + self.current_battery <= self.max_battery + DELTA:
            assert False, f"Battery amount invalid!, charge {battery_charge} to {battery_charge + self.current_battery}!"
        solar = Table.iloc[self.step]["UnitSolar"]  # 单位面积太阳能发电量
        energy = Table.iloc[self.step]["Consume"]  # 用电量
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
        wasted = 0
        if pv > energy / self.cost_effi:
            wasted = pv - energy / self.cost_effi
        pv = min(pv, energy / self.cost_effi)
        pg = (energy - pv * self.cost_effi - bo * self.cost_effi * self.cost_effi) / self.cost_effi
        self.current_battery += battery_charge
        self._add_result(pv, bi, bo, pg, wasted)
        self.step += 1

    def get_data(self):
        return {
            "time": Table.iloc[self.step]["DateTime"],
            "battery": self.current_battery,
            "solar": Table.iloc[self.step]["UnitSolar"] * self.solar_size,
            "consume": Table.iloc[self.step]["Consume"]
        }

    def get_result(self):
        cost = (Table["energy_pg"] * Table["PriceUnit"]).sum()
        return cost + self.convert_cost + self.solar_cost + self.battery_cost

    def get_json(self):
        system_process = []
        for index, row in Table.iterrows():
            val = {}
            val["energy_pv"] = float(round(row["energy_pv"], 4))
            val["energy_bi"] = float(round(row["energy_bi"], 4))
            val["energy_bo"] = float(round(row["energy_bo"], 4))
            val["energy_pg"] = float(round(row["energy_pg"], 4))
            val["date_time"] = row["DateTime"]
            val["radiation"] = row["Radiation"]
            val["temperature"] = row["Temperature"]
            val["consume"] = row["Consume"]
            system_process.append(val)

        return json.dumps({
            "battery_number": self.battery_number,
            "pv_area": self.solar_size,
            "cost": round(self.get_result(), 4),
            "system_result": system_process,
        })


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


def get_time_list(input_list):
    segment = {1: (5, 7), 2: (8, 11), 3: (12, 16), 4: (21, 4 + 24)}  # 17~20 insert
    time_list = [0] * 5
    for idx, val in enumerate(input_list):
        now = idx % 4 + 1
        num = segment[now][1] - segment[now][0] + 1
        time_list += [val] * num
        if now == 3:
            time_list += [0, 0, 0, 0]  # 17~20
    return time_list


# 0 : use battery
# 1 : no use battery
def zws_stra(solar, battery, input_list: list):
    sy = System(solar, battery)
    time_list = get_time_list(input_list)
    for i in range(24 * 31):
        data = sy.get_data()
        if data["solar"] * sy.cost_effi > data["consume"]:
            sy.update(max(
                (min((data["solar"] * sy.cost_effi - data["consume"]), sy.max_battery - data["battery"]) - DELTA)
                , 0))
        else:
            if time_list[i] == 0:  # use battery
                sy.update(-min((data["consume"] - data["solar"] * sy.cost_effi) / sy.cost_effi / sy.cost_effi, data["battery"]))
            else:  # no use battery
                sy.update(0)
    return sy


# Table = init_table()
# s = System(2861, 158)
# sb_stra(s)
# print(round(s.get_result(), 4))

# Table = init_table()
#
good_list = [0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1,
             1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0,
             1, 0]
# list_by_hour = get_time_list(good_list)[:745]
# sy = zws_stra(2860, 158, good_list)

plt.rcParams["date.autoformatter.day"] = "%m-%d"


def base_line():
    sy = System(0, 0)
    for i in range(24 * 31):
        sy.update(0)
    return sy


def plot_base_line():
    global Table
    Table = init_table()
    sy = base_line()

    time_span = []
    time_span_day = []
    day_cost = [0] * 31
    for idx, row in Table.iterrows():
        if row["DateTime"].day not in time_span_day:
            time_span.append(row["DateTime"])
            time_span_day.append(row["DateTime"].day)
        day_cost[row["DateTime"].day - 1] += row["energy_pg"] * row["PriceUnit"]

    plt.plot(time_span, day_cost, label="BaseLine")
    # plt.plot(Table["DateTime"], Table["Consume"], label="Consume")
    # plt.plot(Table["DateTime"], Table["waste_solar"], label="WasteSolar")
    # plt.legend()
    # plt.ylim(0, 2400)
    # plt.title("Only grid power")
    # plt.show()


plot_base_line()


def solar_only():
    sy = System(2888, 0)
    for i in range(24 * 31):
        sy.update(0)
    return sy


def plot_solar_only():
    global Table
    Table = init_table()
    sy = solar_only()

    time_span = []
    time_span_day = []
    day_cost = [0] * 31
    for idx, row in Table.iterrows():
        if row["DateTime"].day not in time_span_day:
            time_span.append(row["DateTime"])
            time_span_day.append(row["DateTime"].day)
        day_cost[row["DateTime"].day - 1] += row["energy_pg"] * row["PriceUnit"] + 400 / 24

    plt.plot(time_span, day_cost, label="Solar only")

    # plt.plot(Table["DateTime"], Table["Consume"], label="Consume")
    # plt.plot(Table["DateTime"], Table["waste_solar"], label="WasteSolar")
    # plt.legend()
    # plt.ylim(0, 600)
    # plt.title("Solar panel direct supply")
    # plt.show()


plot_solar_only()


def plot_sb():
    global Table
    Table = init_table()
    sy = System(2860, 158)
    sb_stra(sy)

    time_span = []
    time_span_day = []
    day_cost = [0] * 31
    for idx, row in Table.iterrows():
        if row["DateTime"].day not in time_span_day:
            time_span.append(row["DateTime"])
            time_span_day.append(row["DateTime"].day)
        day_cost[row["DateTime"].day - 1] += row["energy_pg"] * row["PriceUnit"] + 400 / 24

    plt.plot(time_span, day_cost, label="Battery")

    # plt.plot(Table["DateTime"], Table["Consume"], label="Consume")
    # plt.plot(Table["DateTime"], Table["waste_solar"], label="WasteSolar")
    # plt.legend()
    # plt.ylim(0, 600)
    # plt.title("Consumption first, Battery sleep at night")
    # plt.show()


plot_sb()


def plot_zws():
    global Table
    Table = init_table()
    sy = zws_stra(2860, 158, good_list)

    time_span = []
    time_span_day = []
    day_cost = [0] * 31
    for idx, row in Table.iterrows():
        if row["DateTime"].day not in time_span_day:
            time_span.append(row["DateTime"])
            time_span_day.append(row["DateTime"].day)
        day_cost[row["DateTime"].day - 1] += row["energy_pg"] * row["PriceUnit"] + 400 / 24

    plt.plot(time_span, day_cost, label="Smart battery")

    # plt.plot(Table["DateTime"], Table["Consume"], label="Consume")
    # plt.plot(Table["DateTime"], Table["waste_solar"], label="WasteSolar")
    # plt.legend()
    # plt.ylim(0, 600)
    # plt.title("Simulated annealing")
    # plt.show()


plot_zws()

plt.legend()
plt.ylim(0, 2400)
plt.title("Cost per Day")
# plt.savefig("./figure/cost_per_day.png", dpi=300)
# plt.show()
plt.clf()

price = [0.450, 0.450, 0.450, 0.450, 0.450, 0.529, 0.529, 0.529, 0.628, 0.628, 0.628, 0.628, 0.529, 0.529, 0.529, 0.529, 0.529, 0.628, 0.628, 0.628, 0.628, 0.450, 0.450, 0.450]
price = list(map(lambda x: x * 6, price))
hour_cost = [0] * 24
for idx, row in Table.iterrows():
    hour_cost[row["DateTime"].hour - 1] += row["UnitSolar"]

plt.scatter(list(range(24)), hour_cost, label="Grid Power Price")
plt.scatter(list(range(24)), price, label="Average Solar Power")
plt.legend()
plt.savefig("./figure/grid_price.png", dpi=300)
plt.show()

# print((Table["energy_pg"] * Table["PriceUnit"]).sum())
# plt.scatter(Table["DateTime"].apply(lambda x: x.hour), Table["battery_after"])
# plt.show()
# for i in range(31):
#     plt.plot(Table["DateTime"].apply(lambda x: x.hour)[i * 24:i * 24 + 24], Table["UnitSolar"][i * 24:i * 24 + 24] * 2860 * 2)
#     plt.plot(Table["DateTime"].apply(lambda x: x.hour)[i * 24:i * 24 + 24], Table["battery_after"][i * 24:i * 24 + 24])
#     plt.show()

# print(i, sy.get_result())
# print(Table["waste_solar"].sum())
#
# Table.to_csv("../others/result.csv")
pass
