import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import scipy.optimize as optimize
from numba import jit, prange


def expDecay(t, N0, tau):
    return(N0 * np.exp(-t/tau))


def gauss_laser(t, mu, sigma):
    return(1/(sigma*np.sqrt(2*np.pi))) * np.exp(-(t - mu)**2/(2*sigma)**2)


def convolutedDecay(t, offset, amp1, tau1, IRFmu, IRFsigma, fitting=False):
    IRF = gauss_laser(t, IRFmu, IRFsigma)
    decay = expDecay(t, amp1, tau1)

    convolvedSignal = np.convolve(IRF, decay, mode='full')[0:len(t)]

    if(fitting == False):  # Set fitting to True to suppress addition of Poisson noise, set True when simulating a decay
        convolvedSignal = addPoissonNoise(convolvedSignal, offset)
    else:
        convolvedSignal += offset

    return(convolvedSignal)


def addPoissonNoise(decay, offset):
    decay = np.random.poisson(decay, len(decay))
    decay += np.random.poisson(offset, len(decay))

    return(decay)

# Objective function


def residuals_convolution(para_est, t, data, weighted=True):
    if(weighted == True):
        weights = 1/np.sqrt(data)
        resids = (data - convolutedDecay(t, *para_est, True))**2 * weights
    else:
        resids = (data - convolutedDecay(t, *para_est, True))**2

    return(resids)


def pixelwiseReconvolution(flimarray, photonthreshold, FLIMInfo):
    # Generating time axis
    tEnd = FLIMInfo['GlobalResolution'] * 1e12
    dt = FLIMInfo['Resolution'] * 1e12
    numBins = math.ceil(tEnd/dt)
    tAxis = np.linspace(0, tEnd, numBins)

    # Initial fit parameter / model guesses
    para_start = (
        20,  # Y-Offset
        75000,  # Amplitude
        4000,  # tau1
        1500,  # Laser shift / mu
        200  # laser sigma
    )

    para_bounds = (
        (0, 1, 10, 100, 100, 10),  # minimum parameter values
        (500, 200000, 10000, 10000, 500)  # maximal parameter values
    )

    para_names = (
        "offset",
        "amp1",
        "tau1",
        "IRFmu",
        "IRFsig"
    )

    opt = optimize.least_squares(
        residuals_convolution,
        para_start,
        args=(tAxis, data, True),  # True enables residuals weighting
        ftol=1e-12,
        xtol=1e-12,
        method='trf',
        loss='cauchy',
        bounds=para_bounds
    )

    return(opt)


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

    lifetimeImage = np.zeros((numDecaysX, numDecaysY), dtype=np.float64)
    tau_fit = []
    tau_cov = []

    for x in prange(numDecaysX):
        for y in range(numDecaysY):
            if(flimarray[x][y][:].sum() > photonthreshold):
                xaxis = np.linspace(0, round(globRes*10E8), flimarray.shape[2])
                maxVal = np.where(
                    flimarray[x][y] == max(flimarray[x][y]))[0][0]
                endOfData = flimarray[x][y].size - rightcutoff
                tau_fit, tau_cov = curve_fit(
                    expDecay, xaxis[maxVal:endOfData], flimarray[x][y][maxVal:endOfData])
                lifetimeImage[x][y] = tau_fit[2]
            else:
                lifetimeImage[x][y] = 100

    return(lifetimeImage)


# @jit(nopython = True)
def globalTailFit(flimarray, FLIMInfo, showPlot=True):
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
        plt.text(1/2*max(xaxis), max(overallDecay)/2,
                 "Fitted Lifetime: %f ns" % lifetime)
        plt.plot(xaxis[maxVal:endOfData-20],
                 expDecay(xaxis, *tau_fit)[maxVal:endOfData-20], 'r-')

        plt.show()

    return(lifetime)


# @jit(nopython = True)
def globalTailFit_wOptimize(flimarray, FLIMInfo, showPlot=True):
      # There's definitely a smarter way to do this.
    overallDecay = np.sum(np.sum(flimarray, axis=0), axis=0)
    xaxis = np.linspace(
        0, round(FLIMInfo['GlobalResolution']*10E8), flimarray.shape[2])
    maxVal = np.where(overallDecay == max(overallDecay))[0][0]
    endOfData = overallDecay.size - 1
    plt.plot(xaxis, overallDecay, 'b.')

    # tau_fit, tau_cov = curve_fit(
    #    expDecay, xaxis[maxVal:endOfData-20], overallDecay[maxVal:endOfData-20], p0=(max(overallDecay), 0, 5))

    tau_fit

    lifetime = round(tau_fit[2], 4)

    if(showPlot == True):
        plt.text(1/2*max(xaxis), max(overallDecay)/2,
                 "Fitted Lifetime: %f ns" % lifetime)
        plt.plot(xaxis[maxVal:endOfData-20],
                 expDecay(xaxis, *tau_fit)[maxVal:endOfData-20], 'r-')

        plt.show()

    return(lifetime)
