import numpy as np
import matplotlib.pyplot as plt

battery = list(range(60, 159, 5))
solar = list(range(1, 3500, 100))
cost = []
minimum = 10000000000
idx = -1
with open("./result.txt", "r") as file:
    for i in file:
        i = i.strip("\n").split(",")
        cost.append(float(i[-1]))
        if float(i[-1]) < minimum:
            minimum = float(i[-1])
            idx = i

X, Y = np.meshgrid(solar, battery)
Z = np.array(cost).reshape(X.shape)
ax = plt.figure().add_subplot(projection='3d')
surf = ax.plot_surface(X, Y, Z, linewidth=0)
plt.savefig("./result.png", dpi=300)
plt.show()
print(min(cost))
print(idx)
