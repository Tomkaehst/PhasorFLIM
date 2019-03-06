setwd("/Users/tomkache/Documents/Studium/Biochemistry/Master Thesis/Data Evaluation/PhasorFLIM/")


source("functions/phasorFunctions/phasorTransforms.R")
source("functions/phasorFunctions/simulateFLIMArray.R")
source("functions/modelFunctions/laserFunctions.R")
source("functions/modelFunctions/monoDecayODE.R")

testArrNum = generateFLIMarraynumerical(dimX = 10, dimY = 10, dimT = 1000, timeMax = 25000, tau = 2500, noise = 100)
plot(testArrNum[[2]][3, 5, ], type = "l")

test_eval = gsTransform(testArrNum, angFrequency = 2*pi*40e06)
plotUniCircle()
points(test_eval, pch = 4)
