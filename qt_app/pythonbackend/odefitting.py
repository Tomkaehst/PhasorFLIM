

def da_flim_ODE(y, t, pars):
    try:
        kf_D = pars['kf_D'].value  # Donor lifetime
        k_r = pars['k_r'].value  # transfer rate
        kf_A = pars['kf_'].value  # acceptor lifetime
        kf_D = pars['kf_D'].value
        kf_D = pars['kf_D'].value
