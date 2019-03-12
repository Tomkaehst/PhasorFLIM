




library(deSolve)
source("functions/modelFunctions/laserFunctions.R")

# Generates monoexponential fluorescence decay from ODE model
# the system is comprised of a donor and an acceptor molecule
doubleDecayArr = function(whichCol, timeMax, timeSteps, tau1, tau2, tauFRET, noise) {
  time = seq(0, timeMax, length.out = timeSteps)
  yIni = c(D1 = 0,
           D0 = 100000,
           A1 = 0,
           A1 = 100000)
  par = c(f1 = tau1 + rnorm(1)*noise,
          f2 = tau2 + rnorm(1)*noise,
          r = tauFRET)
  
  model = function(time, yIni, par) {
    with(as.list(c(yIni, par)), {
      laser = laser.gauss(
        time,
        amp = 150,
        dplace = 0,
        grsm = 100
      )
      
      dD1 = -(1/f1 + 1/r)*D1 + laser
      dD0 = -dD1
      dA1 = (1/r)*D1 - (1/f2)*A1
      dA0 = -dA1
      list(c(dD1, dD0, dA1, dA0))
    })
  }
  
  output = ode(func = model,
               times = time,
               y = yIni,
               parms = par,
               method = "lsoda")
  
  return(output[, whichCol])
}

