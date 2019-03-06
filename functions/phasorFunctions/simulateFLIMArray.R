#########################################
# Functions to simulate FLIM data       #
# in a 3D array for method evaluation.  #
# Tom Kache,                            #
# Jena, 2019                            #
#########################################


generateFLIMarray = function(dimX = 20, dimY = 20, dimT = 1000, timeMax = 25000, tau = 2000, noise = 0.02) 
  {
  
  # Preallocating memory for 3D FLIM array
  FLIMarr = array(0, dim = c(dimX, dimY, dimT))
  time = seq(0, timeMax, length.out = dimT)
  
  for(i in 1:length(decayArray[, 1, 1])) {
    for (j in 1:length(decayArray[1, , 1])) {
      FLIMarr[i, j, ] = exp(-time/(tau + rnorm(1)*(100*noise))) + rnorm(length(FLIMarr[1, 1, ]))*noise
    }
  }
}


# Generate FLIM array using a numerically integrated model (see modelFunctions folder)
generateFLIMarraynumerical = function(dimX = 20, dimY = 20, dimT = 1000, timeMax = 25000, tau = 2000, noise = 200) {
  source("modelFunctions/monoDecayODE.R")
  
  # Preallocating memory for 3D FLIM array
  FLIMarr = array(0, dim = c(dimX, dimY, dimT))
  time = seq(0, timeMax, length.out = dimT)
  
  for(i in 1:length(decayArray[, 1, 1])) {
    for (j in 1:length(decayArray[1, , 1])) {
      FLIMarr[i, j, ] = monoDecayArr(timeMax, timeSteps = dimT, tau = tau, noise)
    }
  }
}


