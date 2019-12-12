from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt


def lotkavolterra(t, z, a = 1, b = 1, c = 1, d = 1):
    x, y = z
    out = [a*x - b*c*y, -c*y + d*x*y]
    return(out)

#sol = solve_ivp(lotkavolterra, [0, 15], [10, 5], args = (1.5, 1, 1, 3), dense_output = True)
sol = solve_ivp(lotkavolterra, [0, 15], [10, 5])
