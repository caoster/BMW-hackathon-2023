from datetime import datetime, timedelta
from tabulate import tabulate

import pandas as pd

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
    return P_p_t


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
        self.battery = battery
        self.battery_unit_capacity = 10.5 * 0.9
        self.cost_solar = 500
        self.cost_convert = 500
        self.cost_effi = 0.95
        self.max_battery = self.battery * self.battery_unit_capacity
        if self.max_battery > 1500:
            assert False, "Battery size exceeds limit!"
        self.cost_battery = 1200 + 2 * self.battery
        self.current_battery = self.max_battery
        self.electricity_cost = 0

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
        if not 0 <= battery_charge + self.current_battery <= self.max_battery:
            assert False, f"Battery amount invalid!, {battery_charge} to {battery_charge + self.current_battery}!"
        solar = SunlightHistory_data.iloc[self.step]["Electricity"]
        energy = EnergyHistory_data.iloc[self.step]["Consume"]
        if solar * self.cost_effi < battery_charge:
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
        self.current_battery += battery_charge
        # TODO: update battery cycle

        self._add_result(pv, bi, bo, pg)
        self.time += timedelta(hours=1)
        self.step += 1

    def get_data(self):
        return {
            "time": self.time,
            "battery": self.current_battery,
            "solar": SunlightHistory_data.iloc[self.step]["Electricity"],
            "consume": EnergyHistory_data.iloc[self.step]["Consume"]
        }

    def get_result(self):
        print(self.electricity_cost)


cost = 0
for i in range(24 * 31):
    v = EnergyHistory_data.iloc[i]
    d = datetime.strptime(v["DateTime"], "%m/%d/%Y %H:%M")
    cost += calculate_electricity_price(d) * v["Consume"] / 0.95
print(cost)

sy = System(0, 0)
for i in range(24 * 31):
    # print(sy.get_data())
    sy.update(0)
sy.get_result()
