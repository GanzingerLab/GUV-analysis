# Technical documentation GUV analysis code

## Description of the files

* `guvanalysis/`
  * `__init__.py` - dummy file such that the scripts get recognized as a python module
  * `__main__.py` - the file that is executed on calling the module
  * `app.py` - main file that handles everything and operates other files
  * `guvcontrol.py` - script that controls the whole analysis process of a stack, forwards and loads data to/from `guvfinder` and `guvgui`
  * `guvfinder.py` - script for automatically detecting all GUVs in a series
  * `guvgui.py` - script for deselecting unwanted features
  * `parameters.py` - helper file that contains a class with parameters
* `docs/` - contains documentation files
* `.gitignore` - prevents data files etc. from being added to source control server
* `README.md` - some short information on the module
* `requirements.txt` - contains the necessary python modules to be installed by `pip`
* `requirements-dev.txt` - requirements with also development packages, not necessary to run analysis

## Process

* Upon running `python -m guvanalysis` the function `run` in `app.py` gets called, which initiates the main GUI (class `GUI` in `app.py`)
* Upon initialisation of the GUI, the main window is opened that presents the user with the option to start a new analysis or open an existing one (only for nd2 files, not possible for tifs) and the function `start_new_analysis` or `reopen_existing_analysis` gets called, depending on the choice
* The nd2 or tif file is opened by the function `open_nd2` and subsequently processed in `process_nd2`, where the metadata are shown
* After clicking next, the user is asked to select the channels to use for intensity calculation and feature detection within `open_channelselector`, which is then saved by `extract_channelindex`
* The function `open_seriesselector` is called if multiple series (or field of views) are present
* For each of the selected series, the function `launch_GUV_GUI` is called, which initiates an instance of the `GUV_Control` from `guvcontrol.py`
* Within the `GUV_Control` class a new window is initialized in the `initiate_GUI` function that shows all parameter settings, buttons and plotting windows, which are passed on to the correct functions in the `guvfinder` and `guvgui`
* The other functions within the `GUV_Control` class are only to update the figures and labels and starting analysis by the `guvfinder`
* Within `guvfinder.py` two classes are present, the first one (`helpers`) sets some helper functions for file conversion, taking subregions of images, etc. The real analysis is performed by the `GUV_finder` class
* Within the `run_analysis` function, the order of analysis can be found, but first GUVs are detected among all frames by the Canny edge detection algorithm, then their are linked together to group points belonging to the same GUV along the frame-axis (= z-axis), for an explanation of the algorithm, see Roy's internship report and the comments in the code
* The linked groups are converted to GUVs by filtering them based on a minimum number of points within `get_GUVs_from_linked_points`
* The user filtering is carried out in `guvgui.py`, it makes use of a matplotlib `imshow` that has scroll and click listeners (functions `_onscroll_guvselector` and `_onclick_guvselector`, resp.)
