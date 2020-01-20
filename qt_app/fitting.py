import flimdata
import numpy as np
from scipy.optimize import curve_fit
from numba import njit

class fitter:

    def __init__(self, flimArray = None, fitSettings = None, timeAxis = None):



        self.data = flimArray
        self.timeAxis = timeAxis
        self.settings = fitSettings

        self.guessedParameters = []
        self.fittedParameters = []

        print(self.timeAxis)

    @staticmethod
    @njit
    def expDecay_mono(x, a, b, tau):
        return(a * np.exp(-x/tau) + b)

    def pixelwise_fit(self, photonthreshold, rightcuttoff):

        print(self.data.shape)

        numdecays_x = self.data.shape[0]
        numdecays_y = self.data.shape[1]

        lifetime_image = np.zeros((numdecays_x, numdecays_y), dtype = np.int32)

        tau_fit = []
        tau_cov = []

        for x in range(numdecays_x):
            for y in range(numdecays_y):
                if(self.data[x][y][:].sum() > photonthreshold):
                    max_value = np.where(self.data[x][y] == max(self.data[x][y]))[0][0]
                    end_of_data = self.data[x][y].size - rightcuttoff

                    try:
                        tau_fit = curve_fit(
                            self.expDecay_mono,
                            self.timeAxis[max_value:end_of_data],
                            self.data[x][y][max_value:end_of_data][0]
                        )
                        lifetime_image[x][y] = tau_fit[2]
                    except:
                        lifetime_image[x][y] = 100

                else:
                    lifetime_image[x][y] = 100

        return(lifetime_image)