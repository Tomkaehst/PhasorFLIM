# AGBP FLIM Fitter - Fluorescence Decay Analysis Software

## Project Description

<center><i></i>Written by Tom Kache & Christoph Biskup, Biomolecular Photonics Group, University Hospital Jena</i></center>

<center><b>Current Verion:</b> 0.5.0, April 23rd 2020</center>

The AGBP FLIM Fitter software is a Python and Qt5-based application, that allows reading and working with TTTR data from the PicoQuant HydraHarp V2. The software is optimized to be used with the Leica TCS SP8 microscope at the Biomolecular Photonics Group at the University Hospital Jena.

## Usage

##### 1. Loading PicoQuant PTU Files






## Development Road Map & To Do List

### Milestones
- [ ] Multi threading and multi processing
    - Currently, the GUI is blocked when calculations are performed. This may confuse the user and might lead to frustration as no cues are given by the software of what is currently being done in the background. This can be achieved by using Python's ```threading``` or ```PyQT5.QThread```.
- [ ] Implement class or function to save and load application settings
  	- Settings like the IRF function used for analysis, user-defined settings for the parameter optimization algorithms, etc. should be saved in a read-able format (e.g. gathering settings from `UI_mainWindow` class, `flimdata` class, and `irf` class and writing them into structured file)
-[ ] Batch processing of data


### To Do

- [ ] Add algorithm for sinusodial correction (see Jupyter notebook)
- [x] Show some information in header of selected `.ptu` file before user loads data into memory
  - [x] User comments should be visible before loading the entire file
  - [x] Show image dimensions from file header
  - Implemented on April 18th 2020
- [ ] Improve output functionalities
  - [x] Include plot of residuals
  - [x] Include option to write selected fluorescence decay, the calculated fit curve, and residuals to CSV output
    - Allows user to re-plot own their own later
    - Implemented on April 22 2020
  - [ ] Include information about IRF used in a particular fit in CSV output file
  - [x] Intensity image - Implemented on April 22nd 2020
- [ ] Allow user to set parameter guesses
- [x] Remove IRF fitting functions
- [x] Add option to chose between using Gauss approximated IRF and measured IRF once IRF has been loaded

  - Implemented on April 18th 2020


## Bug Reports

- [ ] IRF shifting parameter is not varied with measured IRF (April 18th 2020)

  ​	- Resolved on April 22nd 2020, Jacobian step size in `scipy.optimize.minimize` not optimal!

- [ ] Additional ROI added sometimes, when new file is loaded and 'Show Selected Decay' is clicked (April 20th 2020)