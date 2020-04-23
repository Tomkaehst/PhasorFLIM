# AGBP FLIM Fitter - Fluorescence Decay Analysis Software

## Project Description

<center><i></i>Written by Tom Kache & Christoph Biskup, Biomolecular Photonics Group, University Hospital Jena</i></center>

<center><b>Current Verion:</b> 0.5.0, April 23rd 2020</center>

The AGBP FLIM Fitter software is a Python and Qt5-based application, that allows reading and working with TTTR data from the PicoQuant HydraHarp V2. The software is optimized to be used with the Leica TCS SP8 microscope at the Biomolecular Photonics Group at the University Hospital Jena.

## Usage

#### Application Overview

The AGBP FLIM Fitter's workflow is subdivided into `Load`, `IRF`, `Fitting` and `Output`. In general, these are the steps required to perform fluorescence decay analysis. All settings are changed or set in the left panel. Outputs and plots are displayed on the right panel. Fig. 1 shows the application right after startup.

![Overview of the AGBP FLIMFitter showing the application after startup.](/home/tom/Documents/PhD/Repositories/PhasorFLIM/qt_app/Documentation/Images/overview.png)

#### Loading PicoQuant PTU Files

To load Picoquant PTU TTTR files, switch to the Load tab in the left panel and click the `Select File` button. In the file selector window, navigate to the desired file and click `Open`. The file is not loaded into memory right away. First, only the header section is loaded, which allows reading user comments and the original image dimensions.

![Loading](/home/tom/Documents/PhD/Repositories/PhasorFLIM/qt_app/Documentation/Images/Loading.png)

![Loading](/home/tom/Documents/PhD/Repositories/PhasorFLIM/qt_app/Documentation/Images/header_peak.png)

Next, some load settings need to be adjusted. Select the correct channel by using the `Channel` number box. PicoQuant assigns channel IDs starting from $0$. Thus, if the fluorescence was recorded with HyD 1, `Channel` needs to be set to $0$, for HyD 2 to $1$, and so on. `Spatial Binning` controls the dimensions of the FLIM image that is being created from the PTU file. The spatial binning reduced the number of pixels in X and Y by even numbers. For example, if the original image dimension was $512 \ \times \ 512$, a spatial binning factor of $2$ reduced it to $512 \ \times \ 512 \ / \ 2^2 = 128 \ \times \ 128$. The same applies to `Temporal Binning`: this factor reduced the number of bins of the fluorescence decay data. With standard settings, the photon counting hardware uses a decay time bin width of $16 \ ps$. When a laser repetition frequency of $20 \ MHz$ was used, there were $3125$ decay bins used for the decay histogram ($\frac{1}{20 \ MHz} \times 16 \ ps = 50.000 \ ps \times 16 \ ps=  3125$). A temporal binning factor of $1$ reduces the number of bins to $3125 / 2^1 = 1562$. The size of the FLIM image that can be chosen in x and y and the number of bins depends on how much system memory is available on the computer.

After these adjustments, click `Load PTU File` and the intensity image appears on the right panel in the `Intensity Image` tab.



#### Selecting an Image Region for Fluorescence Decay Fitting

Click the `Show Selected Decay` button. A ROI will appear on the intensity image that can be moved by clicking and holding and can be resized by the handle on the bottom right of the ROI. Move and resize the ROI so that the desired image region is selected. Click `Show Selected Decay` again and the fluorescence decay will appear on the right panel in the `Decay` tab. 



#### Loading and Cleaning an IRF for Fitting

*This is still being developed. Fitting with a measured IRF does not work as desired right now. The IRF will be approximated by a Gauss function by default. Right now, an IRF can be loaded and cleaned up for fitting, however the fitting algorithm does not arrive at a proper solution right now.*

To load an IRF file, switch to the `IRF` tab on the left panel and click `Load IRF File`. Once a file has been selected, the IRF plot will be displayed on the right panel. To switch to a logarithmic plot, right click on the plot on the right panel and select `Plot Options` $\rightarrow$ `Transforms` $\rightarrow$ `Log Y`.

![log_plot_menu](/home/tom/Documents/PhD/Repositories/PhasorFLIM/qt_app/Documentation/Images/log_plot_menu.png)

To clean the IRF, use the `Left Cutoff` and `Right Cutoff` number inputs to remove decay bins from the left or right side of the IRF. `Background` will subtract counts from the IRF. Click `Correct IRF` to apply the settings. The IRF will be reset each time `Correct IRF` is clicked, so that the values can be adjusted until a satisfying parameter combination is found.



#### Fitting the Selected Fluorescence Decay

Switch to the `Fitting` tab on the left panel. Right now, three options can be set. The `Objective` drop-down list allows to choose between the Poisson deviance error function or standard least-squares error minimization. Poisson deviance is adjusted for a Poissonian error distribution and yields better results for decays with a low number of photon counts. Least squares is the standard error function for fluorescence decay fitting and assumed Gaussian errors. The Poisson deviance error function is defined as 

$$\chi_{ML} = -2 \sum_{t = 0}^{n} f(t, \bold{\omega}) - d(t) \ log\big[f(t, \bold{\omega})\big])$$

with $f(t, \bold{\omega})$ as the fitted model function, $\bold{\omega}$ as the fitted set of parameters, and $d(t)$ as the measured data.

Standard least-square minimization is done by minimizing

$$\chi_{LS} = \sum_{t = 0}^{n} \frac{\big[d(t) - f(t, \bold{\omega})\big]^2}{f(t, \bold{\omega})}$$



The `No. Exponential` number inputs allows to set the number of decay components. The overall model is defined as

$$f(t) = \Big[ \sum_{i = 1}^{n}A_i e^{-\frac{t}{\tau_i}} \Big] \circledast IRF$$

with $n$ as the number of decay components, $A_i$ as the amplitude of the $ith$ component, and $\tau_i$ as the lifetime of the $ith$ component.

The `Use Measured IRF` check box can be set to use the IRF from the `IRF` tab. Otherwise, it will be approximated by a Gauss function

$$IRF(t) = \frac{1}{\sigma \sqrt{2 \pi}} e^{-\frac{(t - \mu)^2}{2\sigma^2}}$$

with $\sigma$ as the width of the IRF and $\mu$ as time shift.

To fit the data to the selected model, click `Fit Selected Decay` and the fit with the residuals appears on the right panel.

![fit_settings](/home/tom/Documents/PhD/Repositories/PhasorFLIM/qt_app/Documentation/Images/fit_settings.png)

The fitted model parameters and the calculated $\chi^2_{red}$ are printed in the `Fitted Parameters` text box on the bottom of the left panel. If a satisfying fit is not achieved the first time, click `Fit Selected Decay` again. The initial fit parameters are then randomized and might produce a better result.

To switch to a logarithmic plot, right-click on the plot and select `Plot Options` $\rightarrow$ `Transforms` $\rightarrow$ `Log Y`.



#### Saving the Fit Results

Switch to the `Output` tab on the left panel. Several options are available to save the results from the AGBP FLIM Fitter to the hard drive.

<img src="/home/tom/Documents/PhD/Repositories/PhasorFLIM/qt_app/Documentation/Images/output_options.png" alt="output_options" style="zoom: 67%;" />

With the `Save Parameters as CSV` button, the fitted model parameters can be saved as CSV file together with the PTU file header information. The results can then be imported into other applications for further statistical analysis.

<img src="/home/tom/Documents/PhD/Repositories/PhasorFLIM/qt_app/Documentation/Images/libreoffice_parameter_csv.png" alt="libreoffice_parameter_csv" style="zoom:67%;" />

The decay, fitted model function and residuals can be saved as a plot in the PNG format by clicking `Save Plot as PNG` button. `Plot Height` and `Plot Width` can be set to change the plot width and height.

<img src="/home/tom/Documents/PhD/Repositories/PhasorFLIM/qt_app/Documentation/Images/example_fit_plot.png" alt="example_fit_plot" style="zoom:50%;" />

`Save Decay and Fit as CSV` allows to save the selected decay data, the fitted model and the residuals as CSV. This option is useful to re-plot the data in another application like Excel. To avoid mixing up files, the original file name of the PTU is printed in the first row of the CSV.

<img src="/home/tom/Documents/PhD/Repositories/PhasorFLIM/qt_app/Documentation/Images/decay_fit_output_csv.png" alt="decay_fit_output_csv" style="zoom:50%;" />

The intensity image from the `Intensity Image` tab on the right panel can be saved as PNG by clicking `Save Image as PNG`.

<div style="page-break-after: always; break-after: page;"></div>




## Development Road Map & To Do List

### Milestones
- [ ] Multi threading and multi processing
    - Currently, the GUI is blocked when calculations are performed. This may confuse the user and might lead to frustration as no cues are given by the software of what is currently being done in the background. This can be achieved by using Python's ```threading``` or ```PyQT5.QThread```.
- [ ] Implement class or function to save and load application settings
  	- Settings like the IRF function used for analysis, user-defined settings for the parameter optimization algorithms, etc. should be saved in a read-able format (e.g. gathering settings from `UI_mainWindow` class, `flimdata` class, and `irf` class and writing them into structured file)

- [ ] Batch processing of data


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

- [x] IRF shifting parameter is not varied with measured IRF (April 18th 2020)

  ​	- Resolved on April 22nd 2020, Jacobian step size in `scipy.optimize.minimize` not optimal!

- [x] Additional ROI added sometimes, when new file is loaded and 'Show Selected Decay' is clicked (April 20th 2020)