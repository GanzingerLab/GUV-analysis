import tkinter as tk
import tkinter.filedialog as filedialog
from tkinter import ttk
from .guvgui import GUV_GUI
from .guvfinder import GUV_finder
from .parameters import ParameterList
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import pims 
import os


class GUI:
    """Main class of the app that displays the main GUI and starts all other screens and modals"""

    def __init__(self):
        """Initialize the class and prompt for opening an nd2 file
        """
        self.root = tk.Tk()
        self.root.geometry("750x500")
        self.root.title("GUV analysis")
        self.window = tk.Frame(self.root)
        self.window.pack(side="top", fill="both", expand=True)
        self.widgets = {'lblHelp': tk.Label(self.window, text="Select a file to open")}
        self.widgets['lblHelp'].pack(side='top')
        self.parameters = {}
        self.open_nd2()

    def destroy_all(self):
        """Clear all frames and widgets"""

        for k in self.widgets:
            self.widgets[k].destroy()
        self.widgets = {}
        self.window.destroy()
        self.window = tk.Frame(self.root)
        self.window.pack(side="top", fill="both", expand=True)

    def open_nd2(self):
        """Opens the filepicker for an nd2 file and proceeds to the next step"""

        filename = filedialog.askopenfilename(initialdir=".", title="Select file...",
                                              filetypes=(("nd2 files", "*.nd2"), ("All files", "*.*")))
        if filename:
            self.parameters['filename'] = filename
            self.parameters['directory'] = os.path.dirname(filename)
            self.widgets['lblHelp']['text'] = f"You selected {filename}"
            self.process_nd2()

    def process_nd2(self):
        """Loads the nd2 file into the class and obtains and displays the metadata from the file"""

        self.stack = pims.open(self.parameters['filename'])
        if "v" in self.stack.sizes:
            self.stack.bundle_axes = 'vyx'
            self.has_multiple_series = True
        else:
            self.stack.bundle_axes = 'yx'
            self.has_multiple_series = False
        self.stack.iter_axes = 'z'
        self.stack.default_coords['t'] = 0
        tvMeta = ttk.Treeview(self.window)
        tvMeta['columns'] = ("metaval")
        tvMeta.column("#0", width=250)
        tvMeta.column("metaval", minwidth=250)
        tvMeta.heading("#0", text="Key", anchor=tk.W)
        tvMeta.heading("metaval", text="Value", anchor=tk.W)
        for metakey, metaval in self.stack[0].metadata.items():
            if not metaval:
                metaval = '' # replace attributes that can't be parsed with an empty string
            tvMeta.insert('', "end", text=metakey, values=(metaval))
        tvMeta.pack(side=tk.TOP, fill=tk.BOTH,expand=True)
        self.widgets['btnNext'] = tk.Button(self.window, text="Select channel >", command=self.open_channelselector)
        self.widgets['btnNext'].pack(side=tk.TOP)

    def open_channelselector(self):
        self.destroy_all()

        self.widgets['lblHelp'] = tk.Label(self.window, text='Channel to use')
        self.widgets['lblHelp'].grid(column=0, row=0)
        self.widgets['lbChannel'] = tk.Listbox(self.window, selectmode=tk.SINGLE, width=50)
        for i,channel in enumerate(self.stack[0].metadata['channels']):
            self.widgets['lbChannel'].insert(i,channel)
        self.widgets['lbChannel'].activate(0)
        self.widgets['lbChannel'].grid(column=1, row=0)
        if self.has_multiple_series:
            self.widgets['btnNext'] = tk.Button(self.window, text="Select series >", command=self.extract_channelindex)
        else: 
            self.widgets['btnNext'] = tk.Button(self.window, text="Analyse >", command=self.extract_channelindex)
        self.widgets['btnNext'].grid(column=1, row=1)
    
    def extract_channelindex(self):
        """Obtain which channel the user has picked"""
        if len(self.widgets['lbChannel'].curselection()) == 0:
            print("Select a channel")
            return
        self.parameters['channel'] = int(self.widgets['lbChannel'].curselection()[0])
        self.stack.default_coords['c'] = self.parameters['channel']
        self.destroy_all()
        if self.has_multiple_series:
            self.open_seriesselector()
        else:
            self.parameters['selected_series'] = [0] # dummy index for looping
            self.launch_GUV_GUI()

    def open_seriesselector(self):
        """Lets the user pick which series to analyse by showing the middle frame of each series"""
        self.destroy_all()

        self.widgets['tvSeries'] = ttk.Treeview(self.window)
        self.widgets['tvSeries']['columns'] = ("metaval")
        self.widgets['tvSeries'].column("#0", width=250)
        self.widgets['tvSeries'].column("metaval", minwidth=250)
        self.widgets['tvSeries'].heading("#0", text="Image", anchor=tk.W)
        self.widgets['tvSeries'].heading("metaval", text="Series", anchor=tk.W)
        self.widgets['tvSeries'].pack(side="left", fill="both")
        style = ttk.Style(self.window)
        style.configure('Treeview', rowheight=80) # set height a bit larger than the image to allow spacing

        self.widgets['scrollSeries'] = ttk.Scrollbar(self.window, orient="vertical", command=self.widgets['tvSeries'].yview)
        self.widgets['scrollSeries'].pack(side="left", fill="y")
        self.widgets['tvSeries'].configure(yscrollcommand=self.widgets['scrollSeries'].set)
        self.images = [] # for some reason display images only works for members of the class, hence the `self.`
        for i in range(self.stack.sizes['v']):
            self.images.append(ImageTk.PhotoImage(
                Image.fromarray(self.stack[self.stack.sizes['z']//2][i]).convert("RGB").resize((75, 75))))
            self.widgets['tvSeries'].insert('', 'end', iid=i, image=self.images[i], values=[f"Series {i}"])
        
        self.widgets['lblHelp'] = tk.Label(self.window, text='Select multiple by holding the Ctrl key')
        self.widgets['lblHelp'].pack(side='left')
        self.widgets['btnNext'] = tk.Button(self.window, text='Next >',
                                            command=self.extract_seriesindices)
        self.widgets['btnNext'].pack(side='bottom')

    def extract_seriesindices(self):
        """Obtain which series the user has picked"""
        if len(self.widgets['tvSeries'].selection()) == 0:
            print("Select at least one series")
            return
        self.parameters['selected_series'] = list(map(int,self.widgets['tvSeries'].selection()))
        self.destroy_all()
        self.launch_GUV_GUI()

    def launch_GUV_GUI(self):
        """Open the GUV_GUI for every of the chosen series"""
        for i in self.parameters['selected_series']:
            print(f"Analysing series {i}")
            self.stack.bundle_axes = 'yx'
            if self.has_multiple_series:
                self.stack.default_coords['v'] = i
                finderparams = ParameterList(series=i, channel=self.parameters['channel'])
            else:
                finderparams = ParameterList(channel=self.parameters['channel'])
            gui = GUV_finder(self.stack, finderparams)
            data = gui.get_data()
            if not data.empty:
                selector = GUV_GUI(self.stack, data)
                csvfilename = self.parameters['filename'].replace(".nd2","_GUVdata-s%02d.csv" % i)
                selector.store_data(csvfilename)
                print("Data for %d GUVs was written to %s" % (selector.get_data().shape[0],csvfilename))
            else:
                print("No GUVs found in series %d" % i)
        self.quit()

    def mainloop(self):
        """Main loop to display the program"""
        self.window.mainloop()
    
    def quit(self):
        """Exits the program"""
        self.root.quit()


def run():
    """This function is called on executing the python module, it starts the GUI and enters the main loop"""
    gui = GUI()
    gui.mainloop()
