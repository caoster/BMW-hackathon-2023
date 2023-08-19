import random
import math
from model import System, DELTA


# 0 : use battery
# 1 : no use battery
def zws_stra(input_list: list, return_json=False):
    sy = System(2950, 158)
    segment = {1: (5, 7), 2: (8, 11), 3: (12, 16), 4: (21, 4 + 24)} # 17~20 insert
    time_list = [0] * 5
    for idx, val in enumerate(input_list):
        now = idx % 4 + 1
        num = segment[now][1] - segment[now][0] + 1
        time_list += [val] * num
        if now == 3:
            time_list += [0, 0, 0, 0] # 17~20
    for i in range(24 * 31):
        data = sy.get_data()
        if data["solar"] * sy.cost_effi > data["consume"]:
            #sy.update((min((data["solar"] * sy.cost_effi - data["consume"]), sy.max_battery - data["battery"])))
            sy.update(max(
                (min((data["solar"] * sy.cost_effi - data["consume"]), sy.max_battery - data["battery"]) - DELTA)
                , 0))
        else:
            if time_list[i] == 0:  # use battery
                sy.update(-min((data["consume"] - data["solar"] * sy.cost_effi) / sy.cost_effi / sy.cost_effi, data["battery"]))
            else:  # no use battery
                sy.update(0)
    if return_json:
        return sy.get_json()
    return sy.get_result()


class SA:
    def __init__(self, lam, eta, M, T_0, CostFunction):
        self.N = 4 * 31
        self.lam = lam
        self.eta = eta
        self.M = M
        self.T_0 = T_0
        self.C = CostFunction
        self.min = 1e10
        self.best = None
        self.currentCost = None
        self.K = 1

    def run(self) -> tuple[float, [int]]:
        T = self.T_0
        # v = [random.randint(0, 1) for _ in range(self.N)]
        v = [0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0]

        mcount = self.M
        self.currentCost = 1e10
        worse_count = 0 
        worse_take = 0
        while T > 0.001:
            moves = int(self.N * math.atan((T + 10) / 100) * 2 / math.pi)
            print("Temp %.4f mc %d cur %.6f mvs %d" % (T, mcount, self.currentCost, moves))
            idx = random.sample(list(range(self.N)), moves)
            new_v = v.copy()
            for i in idx:
                new_v[i] = random.randint(0, 1)
            new_cost = self.C(new_v)
            difference = new_cost - self.currentCost
            if difference < 0:
                v = new_v
                self.currentCost = new_cost
            else:
                worse_count += 1
                if random.random() < math.exp(-difference / (T * self.K)):
                    worse_take += 1
                    v = new_v
                    self.currentCost = new_cost
            mcount -= 1
            if mcount == 0:
                mcount = self.M
                T *= self.lam
            print(worse_take, worse_count)
            
        result = self.C(v)
        if result < self.min:
            self.min = result
            self.best = v
        
        print(self.min)
        print(self.best)
        return self.min, self.best

if __name__ == "__main__":
    lam = 0.9  # 降温速率
    eta = 0.95  # 终止条件
    M = 12  # Markov重复次数
    T_0 = 10  # 初始温度
    sa = SA(lam, eta, M, T_0, zws_stra)
    while True:
        sa.run()
