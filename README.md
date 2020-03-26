# GUV analysis code
This code provides a way of analysing the confocal microscopy data of giant unilaminar vescicles (GUVs). 
It can open `.nd2` files from the microscope, allows you to select the series you want and then allows you to select the GUVs that you want to analyse.

## Requirements
* You need to have python 3 (>= 3.7) installed

## Installation
* Copy the files to a folder on your pc
* Enter the directory (`cd GUV-analysis`)
* Create a virtual environment for installing the required packages:<br>`python3 -m venv venv`<br>This creates the directory `venv` within the project to store the require packages
* Activate the virtual environment 
    * On Windows: run `venv\Scripts\activate.bat`
    * On Mac/Linux: run `source venv/bin/activate`
* Install the packages<br>`pip install -r requirements.txt`

## Running the code
* Make sure you are in the right environment (See Installation > Activate the virtual environment)
* Start the script with:<br>
`python -m guvanalysis`

If you're done running the code (and closed the program), you can either close the terminal to deactivate the environment or run the following:
* On Windows: run `venv\Scripts\deactivate.bat`
* On Mac/Linux: run `deactivate`