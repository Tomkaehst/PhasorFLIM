'''
 Collection of functions for FLIM data visualization
'''


def showIntensityImage(intensityImageArray, saveImage=False):

    import matplotlib.pyplot as plt

    plt.imshow(intensityImageArray, cmap='gray')

    if(saveImage == True):
        plt.savefig('imgOutput/out.png')

    plt.show()

    return(0)


def showLifetimeImage(lifetimeArray, globalLifetime, lowerLimit=0, upperLimit=5, saveImage=False):

    import matplotlib.pyplot as plt

    plt.imshow(lifetimeArray, cmap='cubehelix_r')
    plt.text(10, 10, globalLifetime)
    plt.clim(lowerLimit, upperLimit)
    plt.colorbar()
    plt.show()

    if(saveImage == True):
        plt.savefig('imgOutput/out.png')

    return(0)
