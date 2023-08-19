import random
import math
from model import System, DELTA


# 0 : use battery
# 1 : no use battery
def zws_stra(input_list: list):
    sy = System(2950, 158)
    segment = {1: (5, 7), 2: (8, 11), 3: (12, 16), 4: (17, 20), 5: (21, 4 + 24)}
    time_list = [0] * 5
    for idx, val in enumerate(input_list):
        num = segment[idx % 5 + 1][1] - segment[idx % 5 + 1][0] + 1
        time_list += [val] * num
    for i in range(24 * 31):
        data = sy.get_data()
        if data["solar"] * sy.cost_effi > data["consume"]:
            sy.update(max(
                (min((data["solar"] * sy.cost_effi - data["consume"]) * sy.cost_effi, sy.max_battery - data["battery"]) - DELTA)
                , 0))
        else:
            if time_list[i] == 0:  # use battery
                sy.update(-min((data["consume"] - data["solar"] * sy.cost_effi) / sy.cost_effi / sy.cost_effi, data["battery"]))
            else:  # no use battery
                sy.update(0)
    return sy.get_result()


class SA:
    def __init__(self, lam, eta, M, T_0, CostFunction):
        self.N = 5 * 31
        self.lam = lam
        self.eta = eta
        self.M = M
        self.T_0 = T_0
        self.C = CostFunction
        self.min = 1e10
        self.best = None

    def run(self) -> tuple[float, [int]]:
        T = self.T_0
        v = [random.randint(0, 1) for _ in range(self.N)]
        mcount = self.M
        while True:
            moves = self.eta * T / self.T_0 * self.N
            if moves < 1:
                break
            idx = random.sample(list(range(self.N)), int(moves))
            new_v = v.copy()
            for i in idx:
                new_v[i] = 1 - new_v[i]
            difference = self.C(new_v) - self.C(v)
            if difference < 0:
                v = new_v
            else:
                if random.random() < math.exp(-difference / T):
                    v = new_v
            mcount -= 1
            if mcount == 0:
                mcount = self.M
                T *= self.lam
        result = self.C(v)
        if result < self.min:
            self.min = result
            self.best = v

        print(self.min)
        print(self.best)
        return self.min, self.best


lam = 0.8  # 降温速率
eta = 0.8  # 终止条件
M = 10  # Markov重复次数
T_0 = 273  # 初始温度
sa = SA(lam, eta, M, T_0, zws_stra)
while True:
    sa.run()
