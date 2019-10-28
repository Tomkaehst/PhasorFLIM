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
        expDecay, xaxis[maxVal:endOfData-20], overallDecay[maxVal:endOfData-20], p0=(max(overallDecay), 0, 5))

    lifetime = round(tau_fit[2], 4)

    plt.text(1/2*max(xaxis), max(overallDecay)/2, "Fitted Lifetime: %f ns" % lifetime)
    plt.plot(xaxis[maxVal:endOfData-20],
             expDecay(xaxis, *tau_fit)[maxVal:endOfData-20], 'r-')

    plt.show()

    return(lifetime)


def expDecay(x, a, b, tau):
    return(a * np.exp(-x/tau) + b)
