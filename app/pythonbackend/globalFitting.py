import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


def globalTailFit(flimarray, FLIMInfo):
      # There's definitely a smarter way to do this.
    overallDecay = np.sum(np.sum(flimarray, axis=0), axis=0)
    xaxis = np.linspace(
        0, round(FLIMInfo['GlobalResolution']*10E8), flimarray.shape[2])
    maxVal = np.where(overallDecay == max(overallDecay))[0][0]
    endOfData = overallDecay.size - 1
    plt.plot(xaxis, overallDecay, 'b.')
    tau_fit, tau_cov = curve_fit(
        expDecay, xaxis[maxVal:endOfData], overallDecay[maxVal:endOfData], p0=(max(overallDecay), 1, 5))

    plt.plot(xaxis, expDecay(xaxis, *tau_fit), 'r-')
    plt.yscale("log")
    plt.show()

    lifetime = round(tau_fit[2], 4)

    return(lifetime)


def expDecay(x, a, b, tau):
    return(a * np.exp(-x/tau) + b)
