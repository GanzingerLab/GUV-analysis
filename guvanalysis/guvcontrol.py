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
from .parameters import ParameterList
from .guvgui import GUV_GUI
from .guvfinder import GUV_finder

class GUV_Control:
    """Graphical User Interface for altering finding parameters and selecting GUVs
    
    Uses the GUV_GUI and GUV_finder
    """

    def __init__(self, stack: ImageSequenceND, parameters: ParameterList, csvfilename: str):
        """Initialize the GUI
        """
        self.stack = stack
        self.stack.bundle_axes = "yx"
        self.stack.iter_axes = "z" # iterate over only z axis, channel should be set in app.py
        self.params = parameters
        self.adjustable_params = self.params.get_adjustable_variables()
        self.resultsfile = csvfilename

        self.initiate_GUI() # launch the GUI

    def initiate_GUI(self):
        self.root = tk.Tk()
        self.root.title("GUV finder tool")

        num_rows = 0
        self.ptitle = tk.Label(self.root, text="Parameters", font="-weight bold -size 16")
        self.ptitle.grid(row=num_rows, column=0, columnspan=2, ipady=3)
        num_rows += 1

        self.plabels,self.pspinners = {},{}
        for variable, props in self.adjustable_params.items():
            self.plabels[variable] = tk.Label(self.root, text=variable)
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
        
        self.rtitle = tk.Label(self.root, text="Results", font="-weight bold -size 16")
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
            tk.Label(self.root, text=title).grid(row=num_rows, column=0,sticky='nw')
            self.rlabels[varname] = tk.StringVar(self.root, value='start analysis...')
            tk.Label(self.root, textvariable = self.rlabels[varname]).grid(row=num_rows, column=1,sticky='ne')
            num_rows += 1

        finishbutton = tk.Button(self.root, text='Save data and quit', command=self.finish)
        finishbutton.grid(row=num_rows, column=0, columnspan=2)
        num_rows += 1

        ttk.Separator(self.root, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=num_rows, sticky='ns', padx=10)
        
        self.statsfig = Figure(figsize=(4,6), dpi=75)
        self.statscanvas = FigureCanvasTkAgg(self.statsfig, self.root)
        self.statscanvas.get_tk_widget().grid(column=3, row=0, rowspan=num_rows, sticky='nswe')

        self.guvfinder = GUV_finder(self.stack, self.params, self.statscanvas, self.statsfig)
        self.guv_data = self.guvfinder.get_data()

        self.scrollfig = Figure(figsize=(6,6), dpi=100)
        self.scrollcanvas = FigureCanvasTkAgg(self.scrollfig, self.root)
        self.scrollcanvas.get_tk_widget().grid(column=4, row=0, rowspan=num_rows, sticky='nswe')

        self.scroller = GUV_GUI(self.stack, self.guv_data, self.scrollcanvas, self.scrollfig)        

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

    def finish(self):
        self.guv_data = self.scroller.get_data()
        if self.guv_data.empty:
            print("No data to store, empty csv file will be written")
        
        print(f"Data for {len(self.guv_data)} GUVs stored in {self.resultsfile}")
        self.guv_data.to_csv(self.resultsfile, index=False, header=True)
        self.root.quit()        

if __name__ == '__main__':
    stack = pims.open("galvano_003_10series.nd2")
    stack.iter_axes = "z"
    stack.bundle_axes = "yx"
    stack.default_coords['t'] = 0
    stack.default_coords['v'] = 8
    stack.default_coords['c'] = 2
    p = ParameterList(series=8, channel=2)
    GUV_Control(stack, p, "galvano_003_10series.csv")