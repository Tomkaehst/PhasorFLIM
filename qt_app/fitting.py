import math
import numpy as np
import scipy.optimize as optimize
from scipy import interpolate
from numba import njit
import matplotlib.pyplot as plt
import multiprocessing as mp

class fitter:
    def __init__(self, time_axis, data, objective_function = None, fit_settings = None):
        self.time_axis = time_axis
        self.data = data
        self.objective_function = objective_function
        self.irf_data = None
        self.irf_function = self.gauss_laser
        self.optimized_parameters = None
        self.lifetime_image = None

        if (fit_settings is None):
            self.decay_parameters = (
                5, # Offset
                np.amax(self.data), # Amplitude
                2500 # tau
            )
            self.IRF_parameters = (
                self.time_axis[np.argmax(self.data)], # IRF Shift, pre-set to time of max peak
                40 # IRF sigma
            )
            self.IRF_fitted_parameters = None # Will hold fitted IRF parameters, if they're passed to self.fit_decay(measured_irf)
            
            # Combining decay parameters and IRF parameters into one tuple
            self.fit_settings = self.decay_parameters + self.IRF_parameters

        else:
            self.fit_settings = fit_settings

        self.parameter_bounds = (
            (0, np.infty),  # Offset
            (0.01, np.infty),# Amplitide
            (50, 10000),  # Tau
            (0, self.time_axis[-1]),# IRF Mu, upper bound is max of time axis
            (0.01, np.infty)  # IRF amplitude
        )

        self.parameter_names = (
            'offset',
            'amplitude',
            'tau',
            'IRF_mu',
            'IRF_sigma',
        )


    def estimate_background(self, data):
        '''
        Calculates median of last 3 % of data.
        Used for weightung of values that have 0 counts, otherwise division will
        lead to NaN.
        '''
        sample_index_right_cutoff = math.floor(len(data) * 0.99)
        sample_index_left_cutoff = math.floor(len(data) * 0.96)

        background = np.median(data[sample_index_left_cutoff : sample_index_right_cutoff])

        return(background)


    def calculate_weights(self, data):
        """

        """

        weights = np.zeros((len(data)))
        weights = 1.0/np.sqrt(data, where = (data != 0))
        weights[np.where(data == 0)] = 1.0/np.sqrt(self.estimate_background(data))

        return(weights)

    @staticmethod
    @njit
    def exp_decay_mono(t, tau):
        """

        """
        return(np.exp(-t/tau))

    @staticmethod
    @njit
    def gauss_laser(t, parameters):
        """
        Calculate Gauss curve using mu (=mean) and sigma (= std. dev.)
        """

        mu = parameters[0]
        sigma = parameters[1]

        gauss = (1/(sigma*np.sqrt(2*np.pi))) * np.exp(-(t - mu)**2/(2*sigma)**2)
        return (gauss)


    def IRF_gauss_convolution(self, time_axis, shift_parameters = None):
        '''
        Calculate convolution of measured IRF and Gauss curve with 
        smallest possible sigma to approximate Dirac delta function.
        ---
        Arguments:
            - time_axis: np.ndarray containing time axis of decay
            - shift_parameters: tuple with IRF_mu and IRF_sigma, only IRF_mu used for shifting
            - irf: np.ndarray containing standardized irf from irf object (irf.py)
        '''

        dirac = np.zeros(time_axis.shape, dtype = np.float64)
        output = np.zeros(time_axis.shape, dtype = np.float64)

        irf_shift = shift_parameters[0]
        pulse_width = (time_axis[1] - time_axis[0]) / 5

        dirac = (1/(pulse_width*np.sqrt(2*np.pi))) * np.exp(-(time_axis - irf_shift)**2/(2*pulse_width)**2)
        dirac /= np.max(dirac)

        output = np.convolve(dirac, self.irf_data)[0:len(time_axis)]

        plt.plot(time_axis, output)
        plt.show()

        return(output)


    def IRF_delta_sifting(self, time_axis, shift_parameters = None):

        print(shift_parameters)

        bin_width = time_axis[1] - time_axis[0]
        irf_shift = shift_parameters[0]
        bin_shift_int = (irf_shift / bin_width)
        bin_shift_fraction = (irf_shift % bin_width) / bin_width

        delta_pulse = np.zeros(self.data.shape, dtype = np.float64)
        delta_pulse[int(bin_shift_int)] = 1 - bin_shift_fraction
        delta_pulse[int(bin_shift_int + 1)] = bin_shift_fraction

        output = np.convolve(delta_pulse, self.irf_data)[0:len(time_axis)]

        plt.plot(output)
        plt.show()

        output /= np.sum(output)

        return(output)


        


    def gauss_laser_multiple_terms(self, t, shift_parameters=None):
        '''
        Generated sum of n Gauss curves.
        -------
        parameters contains fitted IRF parameters from
        irf.fitted_irf() in the form:
        parameters[0]: global time shift, shift whole function
        parameters[1]: mu of 1st component
        parameters[2]: sigma of 1st component
        parameters[3]: mu of 2nd component
        ...
        Here, the fitted IRF is re-generated by summing
        Gauss curves defined by fitted parameters. Function
        loops over length of parameters tuple with step size
        of 2 to catch every parameter pair. First parameter
        in tuple is global time shift of fitted IRF.
        Thus, only global time shift needs to be optimized
        in order to fit decay.
        CAVE: shift_parameters contains two_values, because
        otherwise compatibility of fit_decay with gauss_laser
        and gauss_laser_multiple_terms cannot be garantueed.
        '''
        
        output = np.zeros_like(t)

        parameters = self.IRF_fitted_parameters
        irf_shift = shift_parameters[0]

        for i in range(1, len(parameters), 2):
            output += (1 / (parameters[i + 1] * np.sqrt(2 * np.pi))) * np.exp(-((t - parameters[i]) - irf_shift)** 2 / (2 * parameters[i + 1])** 2)

        output = output / np.max(output)

        return(output)


    def shift_irf_2(self, irf_shift):

        # 1. Find IRF maximum peak: either max peak or where user defined left cut
        # 2. Shift IRF to left side of array -> np.roll
        # 3. Interpolate processed IRF 
        # 4. 
        pass


    def convoluted_decay(self, time_axis, parameters):
        """

        """

        offset, amp, tau = parameters[0:len(self.decay_parameters)]
        IRF_parameters = parameters[len(self.decay_parameters):len(parameters)]

        decay = self.exp_decay_mono(time_axis, tau)
        IRF = self.irf_function(time_axis, IRF_parameters)

        convoluted_signal = np.convolve(IRF, decay)[0:len(time_axis)]
        convoluted_signal *= 10 * amp
        convoluted_signal += offset

        return(convoluted_signal)


    def calculate_residuals(self):
        """

        """
        residuals = ((self.convoluted_decay(self.time_axis, self.optimized_parameters['x']) - self.data)) / np.sqrt(self.data)

        return(residuals)


    def calculate_reduced_chi_square(self):
        '''
        Calculate reduced chi-square based on decay data and fitted model.
        '''
        try:
            fitted_curve = self.convoluted_decay(self.time_axis, self.optimized_parameters)

        except ValueError:
            print('Error occured while calculating reduced chi-square')
        return
            

    ## Objective functions
    def minimization_least_squares(self, start_parameters, time_axis, data, weighted = False):

        fitted = self.convoluted_decay(time_axis, start_parameters)

        if(weighted):
            weights = self.calculate_weights(data)
            with np.errstate(divide = 'ignore'):
                resids = ((data - fitted)**2 * weights) / fitted
        else:
            with np.errstate(divide = 'ignore'):
                resids = ((data - fitted)**2) / fitted
            
        resids = np.sum(resids)

        return(resids)

    def minimize_poisson_deviance(self, start_parameters, time_axis, data):
        """
        From Bajzer et al., 1991
        """
        fitted = self.convoluted_decay(time_axis, start_parameters)
        with np.errstate(divide = 'ignore'):
            deviance = 2 * np.nansum(
                data * np.log(data / fitted) - (data - fitted)
            )
        
        #deviance = np.sum(deviance)

        return(deviance)


    def fit_decay(
        self,
        decay = None,
        measured_irf = None, # Cary over fitted IRF parameters from irf.fitted_irf to re-generate IRF numerically
        irf_fitted_parameters = None,
        minimization_method = 'SLSQP',
        cutoff = 1):
        """

        """

        # Selecting objective function
        if(self.objective_function == 'Least Squares'):
            objective_function = self.minimization_least_squares
        else:
            objective_function = self.minimize_poisson_deviance


        # Check if measured IRF has been defined
        if (measured_irf is None):
            # Pass standard Gauss function as IRF approximation
            self.irf_function = self.gauss_laser
            print('Gauss used for IRF.')
        elif(measured_irf is not None):
            if(irf_fitted_parameters is not None):
                self.irf_function = self.gauss_laser_multiple_terms
                self.IRF_fitted_parameters = irf_fitted_parameters
                print('Fitted n-terms Gauss used for IRF.')
            else:
                self.irf_function = self.IRF_gauss_convolution # Toms version
                #self.irf_function = self.IRF_delta_sifting # Christophs version
                self.irf_data = measured_irf
                print('Measured IRF used.')

        # Trim data according to user-set cutoffs
        decay_trimmed = decay[0:(len(decay) - cutoff)],
        time_axis_trimmed = self.time_axis[0:(len(self.time_axis) - cutoff)]

        # Perform fit while catching Runtime Errors
        try:
            self.optimized_parameters = optimize.minimize(
                objective_function,
                self.fit_settings,
                args = (time_axis_trimmed, decay_trimmed),
                method = minimization_method,
                bounds = self.parameter_bounds,
                options = {
                    'maxiter': 2000,
                    'disp': False
                }
            )
        except RuntimeWarning:
            print('\nFitting unsucessfull. See error message above!\n')

        # Calculate fit with optimized parameters and weigted residuals
        fitted_curve = self.convoluted_decay(self.time_axis, self.optimized_parameters['x'])
        residuals = self.calculate_residuals()

        return(fitted_curve, residuals)





    def fit_image(self, photon_threshold = 100):
        ''' 

        ''' 
        if(len(self.data.shape) < 3):
            raise ValueError('fit object was not initialized with a FLIM array!')

        # Initialzing flat array for optimized values
        lifetime_image = np.zeros((self.data.shape[0] + self.data.shape[1]))

        # Flatten data array to map cores to pixels
        self.data = self.data.flatten()
        self.data = mp.Array('f', self.data)


        #print('Fitting line', x)

        #self.lifetime_image = lifetime_image


    def apply_function_multiprocessing(self, args):
        pass
