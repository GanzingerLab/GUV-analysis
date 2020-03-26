import tkinter as tk
import tkinter.filedialog as filedialog
from .nd2helper import ND2Stack

window = tk.Tk()
window.title("GUV analysis")
label = tk.Label(window, text = "Hello world").pack()

def run():
    window.mainloop()