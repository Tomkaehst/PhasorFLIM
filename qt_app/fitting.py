import flimdata
import numpy as np
import math
import scipy.optimize as optimize
from numba import njit
import matplotlib.pyplot as plt

class fitter:

    def __init__(self, flimArray = None, fitSettings = None, timeAxis = None):



        self.data = flimArray
        self.overall_decay = self.sum_up_flimarray()
        self.timeAxis = timeAxis
        self.settings = fitSettings

        self.guessedParameters = []
        self.fittedParameters = []


    def sum_up_flimarray(self):
        decay = np.sum(np.sum(self.data, axis = 0), axis = 0)
        return(decay)


    def estimate_background(self, data):
        '''
        Calculates median of last 7 % of data.
        Used for weightung of values that have 0 counts, otherwise division will
        lead to NaN.
        '''
        sample_index_right_cutoff = math.floor(len(data) * 0.97)
        sample_index_left_cutoff = math.floor(len(data) * 0.90)

        background = np.median(data[sample_index_left_cutoff : sample_index_right_cutoff])

        return(background)


    def calculate_weights(self, data):

        weights = np.zeros((len(data)))
        weights = 1.0/np.sqrt(data, where = (data != 0))
        weights[np.where(data == 0)] = 1.0/np.sqrt(self.estimate_background(data))

        return(weights)


    def residuals(self, para_est, t, data, weighted = True):
        if(weighted):
            weights = self.calculate_weights(data)
            resids = (data - self.convoluted_decay(t, *para_est, True))**2  * weights
        else:
            resids = (data - self.convoluted_decay(t, *para_est, True))**2

        return(resids)



    @staticmethod
    @njit
    def expDecay_mono(t, N0, tau):
        return(N0 * np.exp(-t/tau))

    @staticmethod
    @njit
    def gauss_laser(t, mu, sigma):
        gauss = (1/(sigma*np.sqrt(2*np.pi))) * np.exp(-(t - mu)**2/(2*sigma)**2)
        return(gauss)


    def convoluted_decay(
        self,
        t,
        offset,
        amp1, 
        tau1, 
        IRFmu,
        IRFsigma,
        scatter
    ):
        IRF = self.gauss_laser(t, IRFmu, IRFsigma)
        IRF_scatter = IRF * scatter
        decay = self.expDecay_mono(t, amp1, tau1)

        convolved_signal = np.convolve(IRF, decay, mode = 'full')[0:len(t)]
        convolved_signal += IRF_scatter

        convolved_signal += offset

        return(convolved_signal)


    ## Objective functions

    def minimization_least_squares(self, para_est, t, data, weighted = True):
        fitted = self.convoluted_decay(t, *para_est)

        if(weighted):
            weights = self.calculate_weights(data)
            resids = ((data - fitted)**2 * weights) / data
        else:
            resids = ((fitted - data)**2) / data

        resids = np.nansum(resids)
        print()

        return(resids)


    def fit_summed_decay(self):
        para_names = (
            "offset",
            "amp1",
            "tau1",
            "mu",
            "sig",
            "scat"
        )

        para_start = (
            self.estimate_background(self.overall_decay),
            5000, # amp1
            2000, # tau 1
            1500, # mu
            100, # sigma
            max(self.overall_decay) * 10 # scatter
        )


        para_bounds = (
            (0,
            1, 
            200,
            10,
            20,
            0),
            (1000,
            500000,
            10000,
            10000,
            500,
            np.infty)
        )

        try:
            para_opt = optimize.least_squares(
                self.minimization_least_squares,
                para_start,
                method = 'trf',
                ftol = 1e-15,
                xtol = 1e-15,
                args = (self.timeAxis, self.overall_decay, False),
                bounds = para_bounds,
                #max_nfev = 10000,
                verbose = 0
            )
        except:
            print('Fitting not possible...\n')
            para_opt = para_start

        #return(para_opt)

        print(para_opt)

        fitted_curve = self.convoluted_decay(self.timeAxis, *para_opt['x'])

        return(fitted_curve)