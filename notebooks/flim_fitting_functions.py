

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
    IRF_scatter = 50000):

    parameter_names = (
        'offset',
        'amplitude',
        'tau',
        'IRF_mu',
        'IRF_sigma',
        'IRF_scatter'
    )

    start_parameters = (
        offset,
        amplitude,
        tau,
        IRF_mu,
        IRF_sigma,
        IRF_scatter
    )

    parameter_bounds = (
        (
            0,
            1,
            200,
            10,
            20,
            0
        ),
        (
            1000,
            500000,
            10000,
            10000,
            500,
            np.infty
        )
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
    return(N * np.exp(-t / tau))

def convoluted_decay(t, offset, amp, tau, IRF_mu, IRF_sigma, IRF_scatter):
    IRF = gauss_laser(t, IRF_mu, IRF_sigma)
    scatter = IRF * IRF_scatter

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
        residuals = (data - convoluted_decay(t, *para_est, True) ** 2) * weights
    else:
        residuals = (data - convoluted_decay(t, *para_est, True) ** 2)

    return(residuals)


def fit_decay(data, t_axis, start_parameters, parameter_bounds):

    optimized_parameters = optimize.least_squares(
        residuals,
        method = 'trf',
        ftol = 1E-15,
        xtol = 1E-15,
        args = (t_axis, data),
        max_nfev = 10000,
        verbose = True
    )

    return(optimized_parameters)

def calculate_fitted_curve(t_axis, optimized_parameters):
    fitted_curve = convoluted_decay(t_axis, *optimized_parameters['x'])
    return(fitted_curve)

def plot_fit(data, t_axis, optimized_parameters, scale = 'log'):
    fitted_curve = calculate_fitted_curve(t_axis, optimized_parameters)
    weighted_residuals = (fitted_curve - data) * calculate_weights(data)

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
        ylabel = 'Weighted Residuals',
        ylim = (min(weighted_residuals * 1.2, max(weighted_residuals) * 1.2))
    )
    ax[1].grid()

    plt.show()

