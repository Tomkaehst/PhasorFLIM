# Decay models. C++ implementation for speed

setwd("/Users/tomkache/Documents/Studium/Biochemistry/Master Thesis/Data Evaluation/PhasorFLIM/")

system("R CMD SHLIB functions/modelFunctions/cpp/monoDecay.c")
dyn.load("functions/modelFunctions/cpp/monoDecay.so")

parms = c(k1 = 2500, k2 = 0)
Y = c(100, 1, 1)
times = seq(0, 25000, 4)

test = ode(Y, times, func = "derivs", parms = parms, dllname = "monoDecay", initfunc = "initmod", nout = 3, outnames = "Sum")
plot(test[, 1], test[, 3],
     type = "l")

