import tkinter as tk
import tkinter.ttk as ttk
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['image.cmap'] = 'gray'
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pims.image_sequence import ImageSequenceND
import nd2reader
import pims
import pandas as pd
from pandas import DataFrame
import os
from .parameters import ParameterList
from .guvgui import GUV_GUI
from .guvfinder import GUV_finder

class GUV_Control:
    """Graphical User Interface for altering finding parameters and selecting GUVs
    
    Uses the GUV_GUI and GUV_finder
    """

    def __init__(self, stack: ImageSequenceND, parameters: ParameterList):
        """Initialize the GUI
        """
        self.stack = stack
        self.stack.bundle_axes = "yx"
        self.stack.iter_axes = "z" # iterate over only z axis, channel should be set in app.py
        self.params = parameters
        self.adjustable_params = self.params.get_adjustable_variables()

        filepath_without_ext = self.params.filename.replace(".nd2","")
        if self.params.series is None:
            self.resultsfilename = filepath_without_ext + "_GUVdata.csv"
            self.paramsfilename = filepath_without_ext + "_GUVparams.json"
        else:
            self.resultsfilename = filepath_without_ext + "_s%02d-GUVdata.csv" % self.params.series
            self.paramsfilename = filepath_without_ext + "_s%02d-GUVparams.json" % self.params.series

        self.initiate_GUI() # launch the GUI

    def initiate_GUI(self):
        self.root = tk.Tk()
        self.root.title("GUV finder tool - series %d - %s" % (self.params.series, self.params.filename))
        self.root.iconbitmap(os.path.join(os.path.dirname(__file__), "icon.ico"))
        self.root.configure(bg='white')
        
        num_rows = 0
        self.ptitle = tk.Label(self.root, bg="white", text="Parameters", font="-weight bold -size 16")
        self.ptitle.grid(row=num_rows, column=0, columnspan=2, rowspan=2, ipady=3)
        num_rows += 2

        self.plabels,self.pspinners = {},{}
        for variable, props in self.adjustable_params.items():
            self.plabels[variable] = tk.Label(self.root, bg="white", text=variable)
            self.pspinners[variable] = ttk.Spinbox(self.root, from_=props['min'], to=props['max'], increment=props['step'])
            self.pspinners[variable].set(props['value'])
            self.plabels[variable].grid(row=num_rows,column=0,sticky='nw')
            self.pspinners[variable].grid(row=num_rows,column=1,sticky='ne')
            num_rows += 1

        analysis_button = tk.Button(self.root, text='Run analysis >', command=self.run_analysis)
        analysis_button.grid(row=num_rows, column=0, columnspan=2)
        num_rows += 1

        ttk.Separator(self.root, orient=tk.HORIZONTAL).grid(column=0, row=num_rows, columnspan=2, sticky='ew', pady=10)
        num_rows += 1
        
        self.rtitle = tk.Label(self.root, bg="white", text="Results", font="-weight bold -size 16")
        self.rtitle.grid(row=num_rows, column=0, columnspan=2, ipady=3)
        num_rows += 1

        result_labels = [ # formatted as (friendly_title, varname)
                ('Number of GUVs', 'num_guvs'),
                ('Average radius (px)', 'avg_radius_px'),
                ('Average radius (μm)', 'avg_radius_um'),
                ('Average intensity', 'avg_intensity'),
            ]
        
        self.rlabels = {}
        for title,varname in result_labels:
            tk.Label(self.root, bg="white", text=title).grid(row=num_rows, column=0,sticky='nw')
            self.rlabels[varname] = tk.StringVar(self.root, value='start analysis...')
            tk.Label(self.root, bg="white", textvariable = self.rlabels[varname]).grid(row=num_rows, column=1,sticky='ne')
            num_rows += 1

        finishbutton = tk.Button(self.root, text='Save data and quit', command=self.finish)
        finishbutton.grid(row=num_rows, column=0, columnspan=2)
        num_rows += 1

        ttk.Separator(self.root, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=num_rows, sticky='ns', padx=10)
        
        self.statslabel = tk.Label(self.root, bg="white", text='')
        self.statslabel.grid(column=3, row=0)

        self.statsfig = Figure(figsize=(4,6), dpi=75)
        self.statscanvas = FigureCanvasTkAgg(self.statsfig, self.root)
        self.statscanvas.get_tk_widget().grid(column=3, row=1, rowspan=num_rows-1, sticky='nswe')

        self.guvfinder = GUV_finder(self.stack, self.params, self.statscanvas, self.statsfig)
        self.guv_data = self.guvfinder.get_data()

        self.scrolllabel = tk.Label(self.root, bg="white", height=3, text="""Use your scrollwheel to scroll through the stack
        All GUVs are represented with blue circles, while the yellow circles indicate GUVs in the current frame
        Right click near a yellow circle to remove it""")
        self.scrolllabel.grid(column=4, row=0, ipady=2)

        self.scrollfig = Figure(figsize=(6,6), dpi=100)
        self.scrollcanvas = FigureCanvasTkAgg(self.scrollfig, self.root)
        self.scrollcanvas.get_tk_widget().grid(column=4, row=1, rowspan=num_rows-1, sticky='nswe')

        self.scroller = GUV_GUI(self.stack, self.guv_data, self.scrollcanvas, self.scrollfig, self.update_stats)        

        self.root.mainloop()

    def run_analysis(self):
        # updating variables 
        for var in self.pspinners:
            val = float(self.pspinners[var].get())
            setattr(self.params, var, val)
        
        self.guvfinder.run_analysis()
        self.guv_data = self.guvfinder.get_data()
        self.scroller.renew(self.guv_data)
        self.fill_results_labels()

    def fill_results_labels(self):
        self.rlabels['num_guvs'].set(len(self.guv_data))
        self.rlabels['avg_radius_px'].set("{:.3g} ± {:.2g}".format(np.mean(self.guv_data['r']), np.std(self.guv_data['r'])))
        self.rlabels['avg_radius_um'].set("{:.4g} ± {:.3g}".format(np.mean(self.guv_data['r_um']), np.std(self.guv_data['r_um'])))
        self.rlabels['avg_intensity'].set("{:.3g}% ± {:.2g}%".format(np.mean(self.guv_data['intensity'])*100, np.std(self.guv_data['intensity'])*100))

    def update_stats(self):
        self.guv_data = self.scroller.get_data()
        self.guvfinder.renew(self.guv_data)
        self.fill_results_labels()

    def finish(self):
        self.guv_data = self.scroller.get_data()
        if self.guv_data.empty:
            print("No data to store, empty csv file will be written")
        
        print(f"Data for {len(self.guv_data)} GUVs stored in {self.resultsfilename}")
        self.guv_data.to_csv(self.resultsfilename, index=False, header=True)
        self.params.to_json(self.paramsfilename)

        self.root.quit()        
