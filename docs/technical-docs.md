---
title: "Techical documentation"
description: "Documentation on how the python code for GUV analysis works"
author: "Roy Hoitink <R.Hoitink@amolf.nl>"
---

# Technical documentation GUV analysis code

## Workflow

1. After typing `python -m guvanalysis` in the console, the `run()` functin in `guvanalysis/app.py` is automatically called
2. The `run()` function initializes a new `tkinter` GUI window that opens a dialog to select a `.nd2` file
3. The `.nd2` file is processed within `process_nd2()`, which means that the correct axes are set over which is iterated, the function also finds out whether there are more than one series included in the file (axis `v`) 
4. The user is presented with the metadata of the file, after which it continues to the window in which the channel for determining the sizes can be selected (witing `open_channelselector()`)
5. If there are multiple series: after clicking the button, the user is redirect to a new window to select one or more series that should be analyzed (select multiple by Ctrl+Left Mouse Button)<br>
If there is only one series, this step is skipped
6. The function `launch_GUV_GUI()` will perform analysis of each of the selected series in the file after which the data is saved into a CSV file with a filename based on the filename of the `.nd2` file. If the file was named `some test file.nd2` the CSV file is saved into the same folder with the name `some test file_GUVdata-s0x.csv` with `x` being the index of the series (starting at 0)

## Description of the files
