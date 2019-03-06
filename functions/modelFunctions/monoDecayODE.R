




library(deSolve)
source("modelFunctions/laserFunctions.R")

# Generates monoexponential fluorescence decay from ODE model (via numerical integration); trivial, but I use it to expand it to more complex decay models
monoDecayArr = function(timeMax, timeSteps, tau, noise) {
  
  time = seq(0, timeMax, length.out = timeSteps)
  yIni = c(D1 = 0,
           D0 = 100000)
  par = c(f = tau + rnorm(1)*noise)
  
  model = function(time, yIni, par) {
    with(as.list(c(yIni, par)), {
      laser = laser.gauss(
        time,
        amp = 0.01,
        dplace = 2500,
        grsm = 100
      )
      
      dD1 = -(1/f)*D1 + laser
      dD0 = -dD1
      list(c(dD1, dD0))
    })
  }
  
  output = ode(func = model,
               times = time,
               y = yIni,
               parms = par,
               method = "lsoda")
  
  return(output[, 2])
}
  
