

# Importing neccessary modules
import numpy as np
import scipy.optimize as optimize
from scipy.integrate import odeint
from lmfit import minimize, Parameter, Parameters, report_fit
import matplotlib.pyplot as plt




def da_flim_ODE(y, t, pars):

    """
    da_flim_ODE(y, t, pars):
        Description:
            - 

        Input: 
            -

        Returns: 
            - 
    """

    try:
        kf_D = pars['kf_D'].value  # Donor lifetime
        k_r = pars['k_r'].value  # transfer rate
        kf_A = pars['kf_'].value  # acceptor lifetime
        sigma = pars['sigma'].value
        offset = pars['offset'].value
    except:
        kf_D, k_r, kf_A, sigma, mu = pars


    def gauss_laser(t, mu, sigma):
        """
            Normalized Gauss curve. Used to approximate laser pulse in FRET-FLIM ODE system.
        """

        out = (1/(sigma*np.sqrt(2*np.pi))) * np.exp(-0.5 * ((t - mu) / sigma)**2)

        return(out)

    dD1 = -kf_D * y[1] - k_r * y[1] + gauss_laser(t) * y[0]
    dD0 = -dD1
    dA1 = -kf_A*y[3] + k_r*y[1]
    dA0 = -dA1

    return([dD0, dD1, dA0, dA1])

def eval_ode(y, t, pars):
    """
    eval_ode(y, t, pars):
        Description:
            - 

        Input:
            - 

        Returns:
            - 
    """

    try:
        offset =  pars['offset'].value
        sim_params = pars
    except:
        offset = pars[5]
        sim_params = pars[0:5]
    
    sol = odeint(da_flim_ODE, y, t, hmax = dt, args = (sim_params, ))
    sol += offset
    
    return(sol)


def residuals(pars, t, data, weighted = False):
    """
        Calculate residuals of donor and acceptor fluorescence decays vs. model defined in da_flim_ODE()

        Input:
            -

        Returns:
            - 1D array of residuals for lmfit.minimize
    """


    model = eval_ode(y0_guess, t, pars)
    
    if(weighted == True):
        weightsD = 1.0/np.sqrt(model[:, 1])
        weightsA = 1.0/np.sqrt(model[:, 3])
        residsD = ((model[:, 1] - data[:, 1]) * weightsD)**2
        residsA = ((model[:, 3] - data[:, 3]) * weightsA)**2
    else:
        resids1 = (model[:, 1] - data[:, 1])**2
        resids2 = (model[:, 3] - data[:, 3])**2
    
    resids = np.hstack((resids1, resids2))

    return(resids)



def fitSimulatedDecay():
    
    # Defining the time axis
    tStart = 0
    tEnd = 50000 # in ps
    dt = 160
    tSteps = (tEnd - tStart) / dt
    t = np.linspace(tStart, tEnd, tSteps)

    # Initial conditions and parameters for donor-acceptor simulation
    sim_y0 = [1000, 0, 1000, 0]

    kf_D = 1/5000 # Donor decay rate
    k_r = 1/10000 # transfer rate between donor and accceptor
    kf_A = 1/1400 # acceptor decay rate
    sigma = 300 # Width of Gauss / Laser pulse
    mu = 5000 # t displacement of laser pulse on nanotime scale
    offset = 0 # y-offset of data

    sim_params = np.array((kf_D, k_r, kf_A, sigma, mu, offset))

    # Simulating decay data
    sim_data = eval_ode(sim_y0, t, sim_params)

    plt.plot(t, sim_data[:, 1], 'b-')
    plt.plot(t, sim_data[:, 3], 'r-')
    plt.show()


    return(0)