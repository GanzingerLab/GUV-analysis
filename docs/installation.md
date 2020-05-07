# Installation

* Copy the files to a folder on your pc
* Enter the directory in which this README file is (`cd GUV-analysis`, do not go into the `guvanalysis` subfolder)
* Create a virtual environment for installing the required packages:<br>`python3 -m venv venv`<br>This creates the directory `venv` within the project to store the require packages
* Activate the virtual environment 
  * On Windows: run `venv\Scripts\activate.bat`
  * On Mac/Linux: run `source venv/bin/activate`
* Install the packages<br>`pip install -r requirements.txt`

## Activation of the virtual environment

Since all packages have only been installed in the virtual environement and not globally in your python installation, you'll need to activate the right environment before executing the scripts, you can do this by running:

* On Windows: run `venv\Scripts\activate.bat`
* On Mac/Linux: run `source venv/bin/activate`

The packages only need to be installed once (as shown above)!

## Deactivation of the virtual environment

Use the following lines in your active terminal to deactivate the virtual environment:

* On Windows: run `venv\Scripts\deactivate.bat`
* On Mac/Linux: run `deactivate`
