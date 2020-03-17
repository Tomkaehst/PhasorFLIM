

import math
from scipy.integrate import odeint
from scipy import optimize
import numpy as np
import matplotlib.pyplot as plt



def sum_up_decay(data):
    decay = np.sum(np.sum(data, axis = 0), axis = 0)
    return(decay)

def make_start_parameters(
    offset = 1,
    amplitude = 50000,
    tau = 2500,
    IRF_mu = 1500,
    IRF_sigma = 100,
    Scatter_amplitude = 50000,
    Scatter_mu = 1500):

    parameter_names = (
        'offset',
        'amplitude',
        'tau',
        'IRF_mu',
        'IRF_sigma',
        'Scatter_amp',
        'Scatter_mu'
    )

    start_parameters = (
        offset,
        amplitude,
        tau,
        IRF_mu,
        IRF_sigma,
        Scatter_amplitude,
        Scatter_mu
    )

    parameter_bounds = (
        [0, 10000],
        [0, np.infty],
        [100, 10000],
        [100, 10000],
        [10, 250],
        [0, np.infty],
        [100, 10000]
    )

    return(parameter_names, start_parameters, parameter_bounds)

def make_time_axis(global_resolution, resolution, number_of_bins = 0):
    t_end = global_resolution * 1E12
    dt = resolution * 1E12
    if(number_of_bins == 0):
        number_of_bins = math.ceil(t_end / dt)

    t_axis = np.linspace(0, t_end, number_of_bins)

    return(t_axis)

def gauss_laser(t, mu, sigma):
    y = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-(t - mu)**2 / (2 * sigma) **2)
    return(y)


def exp_decay(t, N, tau):
    return(1000*N * np.exp(-t / tau))

def convoluted_decay(t, offset, amp, tau, IRF_mu, IRF_sigma, Scatter_amplitude, Scatter_mu):
    IRF = gauss_laser(t, IRF_mu, IRF_sigma)
    scatter = 1000*Scatter_amplitude * gauss_laser(t, Scatter_mu, IRF_sigma)

    decay = exp_decay(t, amp, tau)

    convoluted_signal = np.convolve(IRF, decay, mode = 'full')[0:len(t)]
    convoluted_signal += scatter

    convoluted_signal += offset

    return(convoluted_signal)

def estimate_background(data):
    sample_index_right_cutoff = math.floor(len(data) * 0.97)
    sample_index_left_cutoff = math.floor(len(data) * 0.90)

    background = np.median(
        data[sample_index_left_cutoff : sample_index_right_cutoff]
    )

    return(background)

def calculate_weights(data):
    weights = np.zeros(len(data))
    weights = 1.0 / np.sqrt(data, where = (data != 0))
    weights[np.where(data == 0)] = 1.0 / np.sqrt(estimate_background(data))
    return(weights)


def residuals(para_est, t, data, weighted = True):

    if(weighted):
        weights = calculate_weights(data)
        residuals = (data - convoluted_decay(t, *para_est) ** 2) * weights
    else:
        residuals = (data - convoluted_decay(t, *para_est) ** 2)

    return(residuals)


# def fit_decay(data, t_axis, start_parameters, parameter_bounds):

#     optimized_parameters = optimize.least_squares(
#         residuals,
#         start_parameters,
#         method = 'lm',
#         ftol = 1E-25,
#         xtol = 1E-15,
#         args = (t_axis, data),
#         max_nfev = 10000,
#         #bounds = parameter_bounds,
#         verbose = True
#     )

#     return(optimized_parameters)


def minimize_poisson_deviance(start_parameters, t, data):
    ''' See Bajzer et al., 1991; Equation 8 '''
    fitted = convoluted_decay(t, *start_parameters)
    
    deviance = 2 * np.nansum(
        data * np.log(data / fitted) - (data - fitted)
    )
    
    return(deviance)


def fit_decay(data, t_axis, start_parameters, parameter_bounds, minimization_method = 'Nelder-Mead', cutoff = 1):
    data_trimmed = data[0:(len(data) - cutoff)],
    t_axis_trimmed = t_axis[0:(len(t_axis) - cutoff)]

    optimized_parameters = optimize.minimize(
        minimize_poisson_deviance,
        start_parameters,
        args = (t_axis_trimmed, data_trimmed),
        method = minimization_method,
        bounds = parameter_bounds,
        options = {
            'maxiter': 1000,
            'disp': False
        }
    )

    return(optimized_parameters)


def calculate_fitted_curve(t_axis, optimized_parameters):
    fitted_curve = convoluted_decay(t_axis, *optimized_parameters['x'])
    return(fitted_curve)

def plot_fit(data, t_axis, optimized_parameters, cutoff, scale = 'log'):

    data = data[0:(len(data) - cutoff)]
    t_axis = t_axis[0:(len(t_axis) - cutoff)]

    fitted_curve = calculate_fitted_curve(t_axis, optimized_parameters)
    weighted_residuals = (fitted_curve - data) * calculate_weights(data)

    reduced_chi_squares = (np.sum((data - fitted_curve)**2 / fitted_curve)) / (len(t_axis - len(optimized_parameters)))

    fig, ax = plt.subplots(2, 1, sharex = True)

    ax[0].plot(t_axis, data, 'r.', label = 'Data')
    ax[0].plot(t_axis, fitted_curve, 'b-', label = 'Fit')
    ax[0].set(
        yscale = scale,
        ylabel = 'Counts'
    )
    ax[0].grid()
    ax[0].legend(loc = 'best')
    
    ax[1].plot(t_axis, weighted_residuals)
    ax[1].set(
        xlabel = 'time [ps]',
        ylabel = 'Weighted Residuals'#,
        #ylim = (min(weighted_residuals * 1.2, max(weighted_residuals) * 1.2))
    )
    ax[1].grid()

    print('Reduced Chi-Squared:', reduced_chi_squares)

    plt.show()

