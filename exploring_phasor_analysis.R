###############################
# Only for testing purposes!  #
# Tom Kache,                  #
# Jena, 2019                  #
###############################


# For function implementations of the script below, see functions folder!


# Exploring phasor anlysis of FLIM data using simulated decays
# Implementation follows Digman et al., 2008

# 1. Generating an array of fluorescence decays with distribution of lifetimes

## Preallocating memory for array 🤓
decayArray = array(0, dim = c(20, 20, 1000)) # I don't quite get the relationship between the angular frequency and the time bin distance!


## Populating the array with simulated decays
timeSim = seq(0, 25000, length.out = length(decayArray[1, 1, ])) # Note: It is important to save the time-axis dimensions somewhere else! We now have a distance of 4 ps between data points in the array!

for(i in 1:length(decayArray[, 1, 1])) {
  for (j in 1:length(decayArray[1, , 1])) {
    decayArray[i, j, ] = exp(-timeSim/(1000*i + rnorm(1)*0.01)) + rnorm(length(decayArray[1, 1, ]))/200
  }
}
#plot(decayArray[1, 1, ], log = "y")

## Implementation of phasor transformation
### calculating g(omega) and s(omega) --> see Digman et al., 2008

gCoordinate = function(array, timeaxis = timeSim, angFrequency = (2*pi*40e06)) { # angular frequecy of 20 MHz pulsed laser
  output = vector(mode = "double", length = (length(array[, 1, 1]) * length(array[1, , 1])))
  
  c = 1 # c keeps track of the index used to save the result in "output"
  for(i in 1:length(array[, 1, 1])) {
    for(j in 1:length(array[1, , 1])) {
      output[c] = sum(array[i, j, ] * cos(angFrequency * timeaxis)) / sum(array[i, j, ])
      c = c + 1
    }
  }
  
  return(output)
}

sCoordinate = function(array, timeaxis = timeSim, angFrequency = (2*pi*40e06)) { # angular frequecy of 20 MHz pulsed laser
  output = vector(mode = "double", length = (length(array[, 1, 1]) * length(array[1, , 1])))
  
  c = 1 # c keeps track of the index used to save the result in "output"
  for(i in 1:length(array[, 1, 1])) {
    for(j in 1:length(array[1, , 1])) {
      output[c] = sum(array[i, j, ] * sin(angFrequency * timeaxis)) / sum(array[i, j, ])
      c = c + 1
    }
  }
  
  return(output)
}

unitCircle  = function(inputArr) {
  time = seq(0, 25000, length.out = length(inputArr[1, 1, ]))
  unitArray = array(0, dim = c(40, 40, length(time)))
  c = 0
  for(i in 1:length(unitArray[, 1, 1])) {
    for (j in 1:length(unitArray[1, , 1])) {
      unitArray[i, j, ] = 1*exp(-time/(c*10))
      c = c + 1
    }
  }
  gCoord = gCoordinate(unitArray, time)
  sCoord = sCoordinate(unitArray, time)
  
  out = data.frame(gCoord, sCoord)
  return(out)
}

testG = gCoordinate(decayArray)
testS = sCoordinate(decayArray)

# plot(unitCircle(decayArray), type = "l",
#      xlim = c(0, 1),
#      ylim = c(0, 0.5))
# Or we just make the computers life more simple
curve(sqrt(0.25-(x - 0.5)^2), from = 0, to = 1,
      xlab = "G",
      ylab = "S")
points(testG, testS,
       pch = 4,
       cex = 0.8,
       col = grey(0.1, 0.2))

