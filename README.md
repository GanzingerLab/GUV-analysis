# GUV analysis code

This code provides a way of analysing the confocal microscopy data of giant unilaminar vescicles (GUVs). 
It can open `.nd2` files from the microscope, allows you to select the series you want and then allows you to select the GUVs that you want to analyse.

## Requirements

* You need to have python 3 (>= 3.7) installed

## Installation

See the [installation file](docs/installation.md) in the docs directory.

## Running the code

* Make sure you are in the right environment (See Installation > Activate the virtual environment)
* Start the script with:

  `python -m guvanalysis`

* Show plots (after analysis has been performed with above command):

  `python -m guvanalysis --show-plots`

* Show module help:

  `python -m guvanalysis -h` (shows all command line options)
  
If you're done running the code (and closed the program), you can either close the terminal to deactivate the environment or follow the steps as described in the [installation file](docs/installation.md)