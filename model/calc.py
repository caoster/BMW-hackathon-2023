# all the direct calculations

# global constants
Capacity = 0.9

# functions

# power of photovoltaic panel
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
    
# battery life decay
def battery_decay(dod, soc, change):
    M_t = 1e-6
    dod_factor = dod / 0.5 if dod <= 0.5 else 1
    soc_factor = 1.05 if soc < 0.3 or soc > 0.8 else 1
    return 1e-4 * dod_factor * soc_factor + (M_t if change else 0)
    
# battery life usage
def use_battery(charge_list):
    sum = 0.0
    diff_next = charge_list[0] - Capacity
    diff_now = 0
    for i in range(len(charge_list)):
        soc = charge_list[i]
        dod = Capacity - soc
        diff_now = diff_next
        diff_next = charge_list[i + 1] - soc if i != len(charge_list) - 1 else 0
        sum += battery_decay(dod, soc, diff_now * diff_next < 0)
        
        