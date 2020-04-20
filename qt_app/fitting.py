# AGBP FLIM Fitter --- Class: fitter
'''
Class Description: fitter()
---------



Authors: Tom Kache & Christoph Biskup, University Hospital Jena
April 2020
'''


import math
import random
import numpy as np
import scipy.optimize as optimize
from numba import njit
import matplotlib.pyplot as plt
import multiprocessing as mp




class fitter:
    def __init__(self,
        time_axis,
        data,
        number_of_exponentials = 1,
        objective_function = None,
        fit_settings = None
        ):

        self.time_axis = time_axis
        self.data = data
        self.number_of_exponentials = number_of_exponentials
        self.objective_function = objective_function
        self.irf_data = None
        self.irf_function = self.gauss_laser
        self.optimized_parameters = None
        self.lifetime_image = None

        if (fit_settings is None):
            self.decay_parameters,\
            self.irf_parameters,\
            self.parameter_names, \
            self.parameter_bounds = self.build_parameter_tuple()
            
            # Combining decay parameters and IRF parameters into one tuple
            self.fit_settings = self.decay_parameters + self.irf_parameters
        else:
            self.fit_settings = fit_settings



    def build_parameter_tuple(self):
        '''
        Builds set of model parameters based on user-chosen number
        of exponential components.
        ------
        self.number_of_exponentials decides about number of
        exponential decay terms used in model for data fitting.
        Structure of parameters
        decay_parameters: contains model paramters
            [0]: offset
            [1]: amplitude first component
            [2]: tau first component
            [3]: amplitude second component
            [4]: tau second component
            ...
        parameter_bounds: bounds for each paramters
        in decay_parameters
        parameter_names: parameter names for display
        irf_parameters: 
            [0]: IRF shift in ps
            [1]: IRF sigma, only used with guessed IRF

        In order to pass parameters to the optimizer 
        (self.fit_decay), decay_parameters and irf_parameters
        have to be combined (using '+') (we need length
        of individual sets to properly work with them
        in model function etc.).
        '''

        decay_parameters = [
            2 # Offset
        ]

        parameter_names = [
            'offset'
        ]

        parameter_bounds = [
             (0, np.infty)
        ]

        for n in range(self.number_of_exponentials):
            # Add model parameters for n-th decay component
            decay_parameters.append(random.randint(100, np.max(self.data))) # Randomizing initial amplitude of component
            decay_parameters.append(random.randint(10, 10000)) # Randomizing initial tau value

            # Add parameter name for n-th decay component
            parameter_names.append('amp' + str(n + 1))
            parameter_names.append('tau' + str(n + 1))

            # Add bounds for n-th decay component
            parameter_bounds.append((0, np.infty))
            parameter_bounds.append((10, 10000))

        # Parameters for Gauss curve approximated IRF
        irf_parameters = [
            2000, # IRF shift
            50 # IRF sigma
        ]

        # Bounds and paramter names for approximated IRF paramters
        parameter_bounds.append((0, self.time_axis[-1]))
        parameter_bounds.append((10, 500))
        parameter_names.append('IRF_shift')
        parameter_names.append('IRF_sigma')

        return(decay_parameters, irf_parameters, parameter_names, parameter_bounds)

            


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
    def exp_decay_mono(time_axis, parameters):
        """
        n-Exponential decay function
        """
        output = np.zeros(time_axis.shape, dtype=np.float64)

        for n in range(1, len(parameters), 2):
            output += (10 * parameters[n] * np.exp(-(time_axis) / parameters[n + 1]))

        return(output)


    @staticmethod
    @njit
    def gauss_laser(time_axis, irf, parameters):
        """
        Calculate Gauss curve using mu (=mean) and sigma (= std. dev.)
        """

        mu = parameters[0]
        sigma = parameters[1]

        gauss = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-(time_axis - mu)** 2 / (2 * sigma)** 2)
        
        return (gauss)


    @staticmethod
    @njit
    def IRF_delta_sifting(time_axis, irf, shift_parameters = None):
        '''
        Shift measured IRF on time axis using delta pulse sifting property
        -----
        Arguments:
            - time_axis
        '''
        bin_width = time_axis[1] - time_axis[0]
        irf_shift = shift_parameters[0]
        bin_shift_int = (irf_shift / bin_width)
        bin_shift_fraction = (irf_shift % bin_width) / bin_width

        delta_pulse = np.zeros(irf.shape, dtype = np.float64)
        delta_pulse[int(bin_shift_int)] = 1 - bin_shift_fraction
        delta_pulse[int(bin_shift_int + 1)] = bin_shift_fraction

        output = np.convolve(delta_pulse, irf)[0:len(time_axis)]

        output /= np.sum(output)

        return(output)


        


    def gauss_laser_multiple_terms(self, time_axis, irf, shift_parameters = None):
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
        
        output = np.zeros(time_axis.shape, dtype = np.float64)

        parameters = self.IRF_fitted_parameters
        irf_shift = shift_parameters[0]

        for i in range(1, len(parameters), 2):
            output += (1 / (parameters[i + 1] * np.sqrt(2 * np.pi))) * np.exp(-((time_axis - parameters[i]) - irf_shift)** 2 / (2 * parameters[i + 1])** 2)

        output = output / np.max(output)

        return(output)


    def convoluted_decay(self, time_axis, parameters):
        """

        """

        decay_parameters = parameters[0:(len(parameters) - len(self.irf_parameters))]
        irf_parameters = parameters[(len(parameters) - len(self.irf_parameters)):len(parameters)]

        decay = self.exp_decay_mono(time_axis, decay_parameters)
        IRF = self.irf_function(time_axis, self.irf_data, irf_parameters)

        convoluted_signal = np.convolve(IRF, decay)[0:len(time_axis)]
        convoluted_signal += parameters[0]

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
            fitted_curve = self.convoluted_decay(self.time_axis, self.optimized_parameters['x'])
            reduced_chi_square = np.sum(((self.data - fitted_curve)**2 / fitted_curve) / (len(self.data) - len(self.fit_settings) - 1))

        except ValueError:
            print('Error occured while calculating reduced chi-square')

        return(reduced_chi_square)



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
        elif(measured_irf is not None):
            if(irf_fitted_parameters is not None):
                self.irf_function = self.gauss_laser_multiple_terms
                self.IRF_fitted_parameters = irf_fitted_parameters
            else:
                #self.irf_function = self.IRF_gauss_convolution # Toms version
                self.irf_function = self.IRF_delta_sifting # Christophs version
                self.irf_data = measured_irf

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
                    'disp': False,
                    'eps': 0.5
                }
            )
        except RuntimeWarning:
            print('\nFitting unsucessful. See error message above!\n')

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
