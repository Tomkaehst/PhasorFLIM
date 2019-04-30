#########################################
# Functions to simulate FLIM data       #
# in a 3D array for method evaluation.  #
# Tom Kache,                            #
# Jena, 2019                            #
#########################################



# Generates FLIM data array with donor and acceptor decay, varying FRET rate (max. in center of rectangular array)

genFLIMarr = function(whichCol = c(2, 4), dimX = 10, dimY = 10, dimT = 1024, timeMax = 25000, tau1 = 2500, tau2 = 1400, FRET_low = 10000, FRET_high = 2000, noise = 10) {
  
  # Preallocating memory for 3D FLIM array
  FLIMarr = array(0, dim = c(dimX, dimY, dimT))
  
  # Array holding the FRET rate for each pixel in FLIMarr
  FRETarr = array(0, dim = c(dimX, dimY))
  
  # Populating dimX x dimY array with varying k_FRET rates
  for(i in 1:dimX) {
    for (j in 1:dimY) {
      FRETarr[j, i] = ((FRET_high - FRET_low)*exp(-(i - dimX/2)^2 / (2*(dimX/12))^2)) + FRET_low
    }
  }
  
  # Generate time axis for simulation
  time = seq(0, timeMax, length.out = dimT)
  
  for(i in 1:length(FLIMarr[, 1, 1])) {
    for (j in 1:length(FLIMarr[1, , 1])) {
      FLIMarr[i, j, ] = doubleDecayArr(whichCol, timeMax, timeSteps = dimT, tau1 = tau1, tau2 = tau2, tauFRET = FRETarr[i, j], noise = 0)
    }
  }
  
  return(list(time, FLIMarr))
}





simFLIMarr_CPP = function(whichCol = c(2, 4), dimX = 5, dimY = 5, dimT = 1000, timeMax = 25000, tau1 = 2500, tau2 = 1400, tau3 = 3000, noise = 0) {
  
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
      FLIMarr[i, j, ] = ode(Y, time, func = "derivs", parms = parms, dllname = "monoDecay", initfunc = "initmod", nout = 2, outnames = "Sum")[,whichCol] + rpois(length(FLIMarr[i, j, ]), lambda = noise)
    }
  }
  
  return(list(time, FLIMarr))
}
