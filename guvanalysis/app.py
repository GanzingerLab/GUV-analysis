import tkinter as tk
import tkinter.filedialog as filedialog
from tkinter import ttk
from .nd2helper import ND2Stack
from .guvgui import GUV_GUI
from PIL import Image, ImageTk


class GUI:
    """Main class of the app that displays the main GUI and starts all other screens and modals
    """
    def __init__(self):
        """Initialize the class and prompt for opening an nd2 file
        """
        self.root = tk.Tk()
        self.root.geometry("750x500")
        self.root.title("GUV analysis")
        self.window = tk.Frame(self.root)
        self.window.pack(side="top", fill="both", expand=True)
        self.widgets = {'lblHelp': tk.Label(self.window, text="Select a file to open")}
        self.widgets['lblHelp'].grid(row=1, columnspan=3, sticky=tk.EW)
        self.open_nd2()

    def destroy_all(self):
        """Clear all frames and widgets
        """
        for k in self.widgets:
            self.widgets[k].destroy()
        self.widgets = {}
        self.window.destroy()
        self.window = tk.Frame(self.root)
        self.window.pack(side="top", fill="both", expand=True)

    def open_nd2(self):
        """Opens the filepicker for an nd2 file and proceeds to the next step
        """
        filename = filedialog.askopenfilename(initialdir=".", title="Select file...",
                                              filetypes=(("nd2 files", "*.nd2"), ("All files", "*.*")))
        if filename:
            self.filename = filename
            self.widgets['lblHelp']['text'] = f"You selected {filename}"
            self.process_nd2()

    def process_nd2(self):
        """Loads the nd2 file into the class and obtains and displays the metadata from the file
        """
        self.stack = ND2Stack(self.filename)
        tvMeta = ttk.Treeview(self.window)
        tvMeta['columns'] = ("metaval")
        tvMeta.column("#0", width=250)
        tvMeta.column("metaval", minwidth=250)
        tvMeta.heading("#0", text="Key", anchor=tk.W)
        tvMeta.heading("metaval", text="Value", anchor=tk.W)
        for k, v in self.stack.get_metadata():
            if not v:
                v = ''
            tvMeta.insert('', "end", text=k, values=(v))
        tvMeta.grid(row=2, rowspan=2, sticky=tk.NE + tk.SW)
        self.widgets['btnNext'] = tk.Button(self.window, text="Select series >", command=self.open_seriesselector)
        self.widgets['btnNext'].grid(row=4, sticky=tk.E)

    def open_seriesselector(self):
        """Lets the user pick which series to analyse by showing the middle frame of each series
        @todo: make the frame scrollable to be able to view many series
        """
        self.destroy_all()
        images = []
        imgdisplays = []
        imglabels = []
        imgcheckvars = []
        for i in range(self.stack.num_series):
            images.append(ImageTk.PhotoImage(
                Image.fromarray(self.stack.get_series_midframe(i, -1)).convert("RGB").resize((50, 50))))
            imgdisplays.append(tk.Label(self.window, image=images[i]))
            imgdisplays[i].image = images[i]
            imgdisplays[i].grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)
            imgcheckvars.append(tk.IntVar())
            imglabels.append(
                tk.Checkbutton(self.window, text=f"series {i}", onvalue=1, offvalue=0, variable=imgcheckvars[i]))
            imglabels[i].grid(row=i, column=2, sticky=tk.W)
        self.widgets['btnNext'] = tk.Button(self.window, text='Next >',
                                            command=lambda: self.extract_seriesindices(imgcheckvars))
        self.widgets['btnNext'].grid(sticky=tk.SE)
        return

    def extract_seriesindices(self, variables=None):
        """Obtain which series the user has picked
        
        Keyword Arguments:
            variables {list} -- List of tk.IntVars() that define which series were picked (default: {None})
        """
        if variables is None:
            variables = []
        self.selected_series = []
        for i, value in enumerate(variables):
            if value.get() == 1:
                self.selected_series.append(i)
        self.destroy_all()
        self.launch_GUV_GUI()

    def launch_GUV_GUI(self):
        """Open the GUV_GUI for every of the chosen series
        """
        for i in self.selected_series:
            print(f"Analysing series {i}")
            GUV_GUI(self.stack, i)

    def mainloop(self):
        """Main loop to display the program
        """
        self.window.mainloop()


def run():
    """This function is called on executing the python module, it starts the GUI and enters the main loop
    """
    gui = GUI()
    gui.mainloop()
