import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import scipy.optimize as optimize
from numba import jit, prange


def expDecay(x, a, b, tau):
    return(a * np.exp(-x/tau) + b)


#@jit(parallel = True)
def pixelwiseSimpleDecay(flimarray, photonthreshold, rightcutoff, globRes):
    '''
        Function: pixelwiseSimpleDecay(
            - flimarray: 3D array x-y-ns holding fluorescence decays for each image pixel
            - photonthreshold: number of photons in pixel required to start fitting
            - rightcuttoff: how much data of decay to exclude from the right side of the curve
            - globRes: FLIMInfo['GlobalResolution'], required to reconstruct time axis with correct time (in ns)
        )
        Returns 2D array lifetimeImage with (flimarray.shape[0] x flimarray.shape[1]) with float64. Holds fitted lifetime values.
        Pixels with photon count below threshold get a lifetime of 100, so that they are clearly distinguished (and not 0)!
    '''
    numDecaysX = flimarray.shape[0]
    numDecaysY = flimarray.shape[1]
    
    lifetimeImage = np.zeros((numDecaysX, numDecaysY), dtype = np.float64)
    tau_fit = []
    tau_cov = []
    
    for x in prange(numDecaysX):
        for y in range(numDecaysY):
            if(flimarray[x][y][:].sum() > photonthreshold):
                xaxis = np.linspace(0, round(globRes*10E8), flimarray.shape[2])
                maxVal = np.where(flimarray[x][y] == max(flimarray[x][y]))[0][0]
                endOfData = flimarray[x][y].size - rightcutoff
                tau_fit, tau_cov = curve_fit(expDecay, xaxis[maxVal:endOfData], flimarray[x][y][maxVal:endOfData])
                lifetimeImage[x][y] = tau_fit[2]
            else:
                lifetimeImage[x][y] = 100
        
    
    return(lifetimeImage)


#@jit(nopython = True)
def globalTailFit(flimarray, FLIMInfo, showPlot = True):
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

    if(showPlot == True):
        plt.text(1/2*max(xaxis), max(overallDecay)/2, "Fitted Lifetime: %f ns" % lifetime)
        plt.plot(xaxis[maxVal:endOfData-20],
             expDecay(xaxis, *tau_fit)[maxVal:endOfData-20], 'r-')

        plt.show()

    return(lifetime)


#@jit(nopython = True)
def globalTailFit_wOptimize(flimarray, FLIMInfo, showPlot = True):
      # There's definitely a smarter way to do this.
    overallDecay = np.sum(np.sum(flimarray, axis=0), axis=0)
    xaxis = np.linspace(
        0, round(FLIMInfo['GlobalResolution']*10E8), flimarray.shape[2])
    maxVal = np.where(overallDecay == max(overallDecay))[0][0]
    endOfData = overallDecay.size - 1
    plt.plot(xaxis, overallDecay, 'b.')
    
    #tau_fit, tau_cov = curve_fit(
    #    expDecay, xaxis[maxVal:endOfData-20], overallDecay[maxVal:endOfData-20], p0=(max(overallDecay), 0, 5))

    tau_fit

    lifetime = round(tau_fit[2], 4)

    if(showPlot == True):
        plt.text(1/2*max(xaxis), max(overallDecay)/2, "Fitted Lifetime: %f ns" % lifetime)
        plt.plot(xaxis[maxVal:endOfData-20],
             expDecay(xaxis, *tau_fit)[maxVal:endOfData-20], 'r-')

        plt.show()

    return(lifetime)
