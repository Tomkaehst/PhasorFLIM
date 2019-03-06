###########################################
# Functions performing phasor transform   #
# of FLIM data stored in a 3d array.      #
# Implementation follows paper:           #
# Digman et al., 2008, Biophys J.         #
# See supplementary material              #
###########################################

#########################
# Tom Kache             #
# Jena, 2019            #
#########################


#########################################################
# G-S transformation                                    #
# Function inputs and explanation:                      #
# gsTransform() performs the phasor transformation for  #
# each pixel in a provided 3D array.                    #
# The transformed data is stored in a data.frame, which #
# is initialized with two colums of lengths array.x     #
# * array.y so it can hold the transformed coordinates  #
# for each decay measured at each pixel.                #
#   - array: 3D input array / FLIM image containing     #
#             the fluorescence decay curve for each     #
#             pixel (x, y)                              #
#   - timeaxis: the time axis of the measured decay     #
#               (add script to synthesize this!)        #
#   -angFrequency: the angular frequency of the         #
#                   excitation source                   #
#                   (2 * pi * laser rep rate)           #
#                                                       #
# Function output is data frame containing the G and S  #
# coordinates of the transformation (G = x-axis;        #
# S = y-axis)                                           #
########################################################




gsTransform = function(array, timeaxis = timeSim, angFrequency = (2*pi*40e06)) {
  output = data.frame(
    G = vector(mode = "double", length = (length(array[, 1, 1]) * length(array[1, , 1]))),
    S = vector(mode = "double", length = (length(array[, 1, 1]) * length(array[1, , 1])))
  )
  
  c = 1 # c keeps track of the index used to save the result in "output"
  for(i in 1:length(array[, 1, 1])) {
    for(j in 1:length(array[1, , 1])) {
      output[[1]][c] = sum(array[i, j, ] * cos(angFrequency * timeaxis)) / sum(array[i, j, ])
      output[[2]][c] = sum(array[i, j, ] * sin(angFrequency * timeaxis)) / sum(array[i, j, ])
      c = c + 1
    }
  }
  
  return(output)
}


#############################
# Quick function that just  #
# displays the universal    #
# circle using R's plot()   #
#############################

plotUniCircle = function() {
  curve(sqrt(0.25 - (x - 0.5)^2), from = 0, to = 1,
        xlab = "S",
        ylab = "G")
}

