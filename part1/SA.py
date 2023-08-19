import random
import math

def CostFunction(strategy):
    pass

class SA:
    def __init__(lam, eta, M, T_0, CostFunction):
        self.N = 5 * 31
        self.lam = lam
        self.eta = eta 
        self.M = M 
        self.T_0 = T_0 
        self.C = CostFunction
        self.min = 1e10
        self.best = None
        
    def run():
        T = self.T_0
        v = [random.randint(0, 1) for i in range(N)]
        mcount = self.M
        while True:
            moves = eta * T / T_0 * N
            if moves < 1:
                break
            idx = random.choice(list(range(N)), moves)
            new_v = v.copy()
            for i in idx:
                new_v[i] = 1 - new_v[i]
            difference = C(new_v) - C(v)
            if difference < 0:
                v = new_v
            else:
                if random.random() < math.exp(-difference / T):
                    v = new_v
            mcount -= 1
            if mcount = 0:
                mcount = self.M 
                T *= lam
        result = C(v)
        if result < min:
            self.min = result
            self.best = v
        