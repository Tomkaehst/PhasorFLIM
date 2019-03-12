#########################################
# Functions to simulate FLIM data       #
# in a 3D array for method evaluation.  #
# Tom Kache,                            #
# Jena, 2019                            #
#########################################


generateFLIMarray = function(dimX = 20, dimY = 20, dimT = 1000, timeMax = 25000, tau = 2000, noise = 0.02) {
  
  # Preallocating memory for 3D FLIM array
  FLIMarr = array(0, dim = c(dimX, dimY, dimT))
  time = seq(0, timeMax, length.out = dimT)
  
  for(i in 1:length(FLIMarr[, 1, 1])) {
    for (j in 1:length(FLIMarr[1, , 1])) {
      FLIMarr[i, j, ] = 1000*exp(-time/(tau)) + rpois(length(FLIMarr[1, 1, ]), lambda = noise)
    }
  }
  # gsTransform() requires knowledge about the time axis; therefore, the output is a list: first element is time axis used for array generation; second element is array itself
  return(list(time, FLIMarr))
}


# Generate FLIM array using a numerically integrated model (see modelFunctions folder)
generateFLIMarraynumerical = function(dimX = 5, dimY = 5, dimT = 1000, timeMax = 25000, tau = 2000, noise = 300) {
  
  # Preallocating memory for 3D FLIM array
  FLIMarr = array(0, dim = c(dimX, dimY, dimT))
  time = seq(0, timeMax, length.out = dimT)
  
  for(i in 1:length(FLIMarr[, 1, 1])) {
    for (j in 1:length(FLIMarr[1, , 1])) {
      FLIMarr[i, j, ] = monoDecayArr(timeMax, timeSteps = dimT, tau = tau, noise = 0) + rpois(length(FLIMarr[1, 1, ]), lambda = noise)
    }
  }
  
  return(list(time, FLIMarr))
}

generateFLIMarraynumericalAcceptor = function(whichCol, dimX = 5, dimY = 5, dimT = 1000, timeMax = 25000, tau1 = 2500, tau2 = 1400, tauFRET = 3000, noise = 300) {
  
  # Preallocating memory for 3D FLIM array
  FLIMarr = array(0, dim = c(dimX, dimY, dimT))
  time = seq(0, timeMax, length.out = dimT)
  
  for(i in 1:length(FLIMarr[, 1, 1])) {
    for (j in 1:length(FLIMarr[1, , 1])) {
      FLIMarr[i, j, ] = doubleDecayArr(whichCol, timeMax, timeSteps = dimT, tau1 = tau1, tau2 = tau2, tauFRET = tauFRET, noise) + rnorm(length(FLIMarr[1, 1, ]))*noise
    }
  }
  
  return(list(time, FLIMarr))
}


generateFLIMarraynumericalTriple = function(whichCol, dimX = 5, dimY = 5, dimT = 1000, timeMax = 25000, tau1 = 2500, tau2 = 1400, tau3 = 3000, tauFRET1 = 3000, tauFRET2 = 2000, noise = 300) {
  
  # Preallocating memory for 3D FLIM array
  FLIMarr = array(0, dim = c(dimX, dimY, dimT))
  time = seq(0, timeMax, length.out = dimT)
  
  for(i in 1:length(FLIMarr[, 1, 1])) {
    for (j in 1:length(FLIMarr[1, , 1])) {
      FLIMarr[i, j, ] = tripleDecayArr(whichCol, timeMax, timeSteps = dimT, tau1 = tau1, tau2 = tau2, tau3 = tau3, tauFRET1 = tauFRET1, tauFRET2 = tauFRET2, noise) + rnorm(length(FLIMarr[1, 1, ]))*noise
    }
  }
  
  return(list(time, FLIMarr))
}






generateFLIMCPPtriple = function(whichCol, dimX = 5, dimY = 5, dimT = 1000, timeMax = 25000, tau1 = 2500, tau2 = 1400, tau3 = 3000, noise = 0) {
  
  # Preallocating memory for 3D FLIM array
  FLIMarr = array(0, dim = c(dimX, dimY, dimT))
  time = seq(0, timeMax, length.out = dimT)
  
  # Loading C implementation of mono decay
  system("R CMD SHLIB functions/modelFunctions/cpp/monoDecay.c")
  dyn.load("functions/modelFunctions/cpp/monoDecay.so")
  
  parms = c(k1 = tau1, k2 = tau2, k3 = tau3)
  Y = c(10000, 0, 0)
  
  for(i in 1:dimX) {
    for (j in 1:dimY) {
      FLIMarr[i, j, ] = ode(Y, time, func = "derivs", parms = parms, dllname = "monoDecay", initfunc = "initmod", nout = 2, outnames = "Sum")[,whichCol]
      parms["k1"] = tau1 + rnorm(1)*noise
      parms["k2"] = tau2 + rnorm(1)*noise
      parms["k3"] = tau3 + rnorm(1)*noise
    }
  }
  
  return(list(time, FLIMarr))
}
