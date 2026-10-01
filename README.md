# PhasorFLIM

Simple implementation of phasor analysis for fluorescence lifetime imaging microscopy (FLIM) analysis. The software enables loading of Picoquant PTU TTTR image files and performs pixel-wise phasor transformation of the contained fluorescence lifetime decay. The phasors are histogrammed on a phasor plot.

The user may select a subpopulation of pixels on the phasor plot and segment the FLIM image based on the phasor mapping. The image can be coloured according to the distribution of phasors by projection of the phasor distribution on the phasor lifetimes. The results can be exported as image and csv files.


![Screenshot of the graphical user interface of the PhasorFLIM software]([Screenshot 2026-10-01 at 10.31.22.png](https://github.com/Tomkaehst/PhasorFLIM/blob/master/Screenshot%202026-10-01%20at%2010.31.22.png))

![Example results: FLIM images of U2OS cells expressing either EGFP only (donor), co-expressing EGFP and mCherry (Co) or a fusion construct mCherry-EGFP. The image colors were obtained by projection of the phasor distribution on a color map.]([Screenshot 2026-10-01 at 10.33.10.png](https://github.com/Tomkaehst/PhasorFLIM/blob/master/Screenshot%202026-10-01%20at%2010.33.10.png))

## Installation

### For Users

To use PhasorFLIM on your machine, download the binaries for your operating system from the releases section of this repo  (https://github.com/Tomkaehst/PhasorFLIM/releases). Currently, Windows and macOS are supported.


### For Development

To install this electronjs app for local development, use ```git clone``` and change to the ```app``` directory.

From there, use 

```npm rebuild```

to get all the dependencies and

```npm start```

to launch the app on your local machine.


## Note
Currently, only PicoQiuant HydraHarp V2 T3 files can be read with this app. Other record types can be implemented.
