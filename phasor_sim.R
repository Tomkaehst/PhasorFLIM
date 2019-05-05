setwd("/Users/tomkache/Documents/Studium/Biochemistry/Master Thesis/Data Evaluation/PhasorFLIM/")

library(deSolve)
source("functions/phasorFunctions/phasorTransforms.R")
source("functions/phasorFunctions/simulateFLIMArray.R")
source("functions/modelFunctions/laserFunctions.R")
source("functions/modelFunctions/monoDecayODE.R")
source("functions/modelFunctions/doubleDecayODE.R")
source("functions/modelFunctions/tripleDecay.R")


# Mono Decay - Analytically
testArrNum = generateFLIMarray(dimX = 3, dimY = 3, dimT = 1024, timeMax = 50000, tau = 2500, noise = 20)
plot(testArrNum[[2]][3, 3, ], type = "l")

test_eval = gsTransform(testArrNum, angFrequency = 2*pi*20e6)
plotUniCircle()
points(test_eval, pch = 4)

# Mono Decay
testArrNum = generateFLIMarraynumerical(dimX = 5, dimY = 5, dimT = 1024, timeMax = 25000, tau = 2500, noise = 0)
plot(testArrNum[[2]][3, 5, ], type = "l")

test_eval = gsTransform(testArrNum, angFrequency = 2*pi*40e6)
plotUniCircle()
points(test_eval, pch = 4)


# Double Decay
testArrNum = generateFLIMarraynumericalAcceptor(whichCol = 2, dimX = 3, dimY = 3, dimT = 1000, timeMax = 25000, tau1 = 2500, tau2 = 1400, tauFRET = 2000, noise = 50)
plot(testArrNum[[2]][1, 1, ], type = "l")

test_eval = gsTransform(testArrNum, angFrequency = 2*pi*40e06)
plotUniCircle(limX = c(0, 1),
              limY = c(0, 1))
points(test_eval, pch = 4)


# Triple Decay

## Donor
testArrNum = generateFLIMarraynumericalTriple(whichCol = 2, dimX = 3, dimY = 3, dimT = 1000, timeMax = 25000, tau1 = 2500, tau2 = 1400, tau3 = 3000, tauFRET1 = 2000, tauFRET2 = 1500, noise = 10)
evalDonor = gsTransform(testArrNum, angFrequency = 2*pi*40e06)
plot(testArrNum[[2]][3, 3, ], type = "l", log = "", lwd = 2)

## Acceptor 1
testArrNum = generateFLIMarraynumericalTriple(whichCol = 4, dimX = 3, dimY = 3, dimT = 1000, timeMax = 25000, tau1 = 2500, tau2 = 2000, tau3 = 3000, tauFRET1 = 2000, tauFRET2 = 1500, noise = 10)
evalAcc1 = gsTransform(testArrNum, angFrequency = 2*pi*40e06)
lines(testArrNum[[2]][3, 3, ], type = "l",
      lty = 3, lwd = 2,
      col = "red")

## Acceptor 2
testArrNum = generateFLIMarraynumericalTriple(whichCol = 6, dimX = 3, dimY = 3, dimT = 1000, timeMax = 25000, tau1 = 2500, tau2 = 1400, tau3 = 3000, tauFRET1 = 2000, tauFRET2 = 1500, noise = 20)
evalAcc2 = gsTransform(testArrNum, angFrequency = 2*pi*40e06)
lines(testArrNum[[2]][3, 3, ], type = "l",
      lty = 3, lwd = 2,
      col = "green")



plotUniCircle(limX = c(0, 1),
              limY = c(0, 1))
points(evalDonor, pch = 2)
points(evalAcc1, pch = 3, col = "red")
points(evalAcc2, pch = 4, col = "green")






# Mono Decay, C implementation (see simulateFLIMArray.R -> generateFLIMCPPmono -> monoDecay.c)
testArrNum = generateFLIMCPPtriple(whichCol = 2, dimX = 40, dimY = 40, dimT = 1000, timeMax = 25000, tau1 = 2000, tau2 = 1400, tau3 = 1500, noise = 500)
plot(testArrNum[[2]][4, 1, ], type = "l")

test_eval = gsTransform(testArrNum, angFrequency = 2*pi*20e06)
plotUniCircle(limX = c(0, 1), limY = c(0, 1))
points(test_eval, pch = 1,
       col = grey(0.2, 0.5))



# FLIM data simulation with varying FRET rates in the "image"
testArrNum = genFLIMarray_da_varFRET(whichCol = 2, dimX = 10, dimY = 10, dimT = 1000, timeMax = 25000, tau1 = 2500, tau2 = 1400, FRET_Start = 15000, FRET_Stop = 5000, noise = 0)
plot(testArrNum[[2]][5, 8, ], type = "l")

test_eval = gsTransform(testArrNum, angFrequency = 2*pi*40e06)
plotUniCircle(limX = c(0, 1), limY = c(0, 1))
points(test_eval, pch = 4,
       col = "red")


