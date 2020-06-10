import tkinter as tk
import tkinter.filedialog as filedialog
from tkinter import ttk
from .guvcontrol import GUV_Control
from .parameters import ParameterList
from .tkhelpers import PhotoImage_cd
from PIL import Image, ImageTk
import pandas as pd
import matplotlib.pyplot as plt
import pims 
import os


class GUI:
    """Main class of the app that displays the main GUI and starts all other screens and modals"""

    def __init__(self):
        """Initialize the class and prompt for opening an nd2 file
        """
        self.root = tk.Tk()
        self.root.minsize(width=150, height=150)
        self.root.maxsize(height=500)
        self.root.title("GUV analysis")
        self.root.iconbitmap(os.path.join(os.path.dirname(__file__), "icon.ico"))
        self.window = tk.Frame(self.root)
        self.window.pack(side="top", fill="both", expand=True)

        self.widgets = {}
        self.images = {}

        self.widgets['lblTitle'] = tk.Label(self.window, text='GUV analysis tool', font="-weight bold -size 20")
        self.widgets['lblTitle'].grid(column=0, row=0, columnspan=3)

        self.images['newImg'] = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__),'icon-new.png')).subsample(2,2)
        self.widgets['btnNew'] = tk.Button(self.window, text='New analysis', image=self.images['newImg'], command=self.start_new_analysis, compound=tk.TOP, borderwidth=0)
        self.widgets['btnNew'].grid(column=0, row=1, padx=10)

        self.images['openImg'] = PhotoImage_cd('icon-open.png').subsample(2,2)
        self.widgets['btnOpen'] = tk.Button(self.window, text='Open existing analysis', command=self.reopen_existing_analysis, image=self.images['openImg'], compound=tk.TOP, borderwidth=0)
        self.widgets['btnOpen'].grid(column=1, row=1, padx=10)

        self.images['closeImg'] = PhotoImage_cd('icon-close.png').subsample(2,2)
        self.widgets['btnClose'] = tk.Button(self.window, text='Close program', command=self.root.quit, image=self.images['closeImg'], compound=tk.TOP, borderwidth=0)
        self.widgets['btnClose'].grid(column=2, row=1, padx=10)
        
    def start_new_analysis(self):
        self.destroy_all()
        self.widgets['lblHelp'] = tk.Label(self.window, text="Select an nd2 file to open")
        self.widgets['lblHelp'].pack(side='top')
        self.parameters = {}
        self.open_nd2()

    def reopen_existing_analysis(self):
        self.destroy_all()
        self.widgets['lblHelp'] = tk.Label(self.window, text="Select a parameters file to open")
        self.widgets['lblHelp'].pack(side='top')
        self.parameters = {}
        filename = False

        while not filename:
            filename = filedialog.askopenfilename(initialdir=".", title="Select parameters file...",
                                              filetypes=(("Parameters file", "*.json"), ("All files", "*.*")))
        params = ParameterList.from_json(filename)
        self.parameters['filename'] = False

        if os.path.exists(params.filename): # check whether the nd2 filename in the json file exists
            self.parameters['filename'] = params.filename

        while not self.parameters['filename']: # if the file does not exists, prompt the user to open the correct file
            print(f"{params.filename} does not exist, pick nd2 file to use")
            self.parameters['filename'] = filedialog.askopenfilename(initialdir=os.path.dirname(filename), title="Select nd2 file...",
                                            filetypes=(("nd2 files", "*.nd2"), ("All files", "*.*")))
            
        datafilename = filename.replace(".json",".csv").replace("GUVparams","GUVdata")
        if not os.path.exists(datafilename):
            datafilename = False
        
        data = pd.read_csv(datafilename, header=0, sep=",")
        if data.empty:
            print("Given datafile is empty, please select another one")
            datafilename = False

        while not datafilename:
            datafilename = filedialog.askopenfilename(initialdir=os.path.dirname(filename), title="Select data file...",
                                            filetypes=(("csv files", "*.csv"), ("All files", "*.*")))
            data = pd.read_csv(datafilename, header=0, sep=",")
            if data.empty:
                print("Given datafile is empty, please select another one")
                datafilename = False
            
        self.stack = pims.open(self.parameters['filename'])
        self.stack.bundle_axes = 'yx'
        self.stack.iter_axes = 'z'
        self.stack.default_coords['c'] = params.channel
        self.stack.default_coords['t'] = 0
        if params.series:
            self.stack.default_coords['v'] = params.series
        
        GUV_Control(self.stack, params, data)
        print("Selected the following files:",filename, self.parameters['filename'], datafilename)
        self.root.quit()


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

        self.widgets['lblHelp'] = tk.Label(self.window, text='Channel for GUV size')
        self.widgets['lblHelp'].grid(column=0, row=0)
        self.widgets['lblIntChHelp'] = tk.Label(self.window, text='Channel for intensity')
        self.widgets['lblIntChHelp'].grid(column=0, row=1)
        self.widgets['lbChannel'] = tk.Listbox(self.window, selectmode=tk.SINGLE, width=50, height = self.stack.sizes['c'], exportselection=0)
        self.widgets['lbIntChannel'] = tk.Listbox(self.window, selectmode=tk.SINGLE, width=50, height = self.stack.sizes['c'], exportselection=0)
        for i,channel in enumerate(self.stack[0].metadata['channels']):
            self.widgets['lbChannel'].insert(i,channel)
            self.widgets['lbIntChannel'].insert(i,channel)
        self.widgets['lbChannel'].selection_set(first=(self.stack.sizes['c'] - 1))
        self.widgets['lbIntChannel'].selection_set(first=0)
        self.widgets['lbChannel'].grid(column=1, row=0, ipady=5)
        self.widgets['lbIntChannel'].grid(column=1, row=1,ipady=5)
        if self.has_multiple_series:
            self.widgets['btnNext'] = tk.Button(self.window, text="Select series >", command=self.extract_channelindex)
        else: 
            self.widgets['btnNext'] = tk.Button(self.window, text="Analyse >", command=self.extract_channelindex)
        self.widgets['btnNext'].grid(column=1, row=2)
    
    def extract_channelindex(self):
        """Obtain which channel the user has picked"""
        if len(self.widgets['lbChannel'].curselection()) == 0 or len(self.widgets['lbIntChannel'].curselection()) == 0:
            print("Select a channel")
            return
        self.parameters['channel'] = int(self.widgets['lbChannel'].curselection()[0])
        self.parameters['intensity_channel'] = int(self.widgets['lbIntChannel'].curselection()[0])
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
        self.root.geometry("750x500")
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
            finderparams = ParameterList(filename=self.parameters['filename'],
                                         channel=self.parameters['channel'],
                                         intensity_channel=self.parameters['intensity_channel'])
            if self.has_multiple_series:
                self.stack.default_coords['v'] = i
                finderparams.series = i
            GUV_Control(self.stack, finderparams) # launch the GUI that can find GUVs and let the user remove them
            
        self.quit()

    def mainloop(self):
        """Main loop to display the program"""
        self.root.mainloop()
    
    def quit(self):
        """Exits the program"""
        self.root.quit()


def run():
    """This function is called on executing the python module, it starts the GUI and enters the main loop"""
    gui = GUI()
    gui.mainloop()
