




library(deSolve)
source("functions/modelFunctions/laserFunctions.R")

# Generates monoexponential fluorescence decay from ODE model
# the system is comprised of a donor and two acceptor molecules (acceptor one is donor for accetor two)
tripleDecayArr = function(whichCol, timeMax, timeSteps, tau1, tau2, tauFRET1, tau3, tauFRET2, noise) {
  time = seq(0, timeMax, length.out = timeSteps)
  yIni = c(D1 = 0,
           D0 = 100000,
           A1 = 0,
           A0 = 100000,
           B1 = 0, 
           B0 = 100000)
  par = c(f1 = tau1 + rnorm(1)*noise,
          f2 = tau2 + rnorm(1)*noise,
          f3 = tau3 + rnorm(1)*noise,
          r1 = tauFRET1,
          r2 = tauFRET2)
  
  model = function(time, yIni, par) {
    with(as.list(c(yIni, par)), {
      laser = laser.gauss(
        time,
        amp = 100,
        dplace = 0,
        grsm = 100
      )
      
      dD1 = -(1/f1 + 1/r1)*D1 + laser
      dD0 = -dD1
      dA1 = (1/r1)*D1 - (1/f2 + 1/r2)*A1
      dA0 = -dA1
      dB1 = (1/r2)*A1 - (1/f2)*B1
      dB0 = -dB1
      list(c(dD1, dD0, dA1, dA0, dB1, dB0))
    })
  }
  
  output = ode(func = model,
               times = time,
               y = yIni,
               parms = par,
               method = "lsoda")
  
  return(output[, whichCol])
}

