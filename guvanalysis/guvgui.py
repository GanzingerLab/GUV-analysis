import tkinter as tk
import tkinter.ttk as ttk
from nd2reader.reader import ND2Reader
import numpy as np
import numpy.linalg as la
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches
from matplotlib.backend_bases import MouseEvent,MouseButton
from scipy.spatial import KDTree
from pims.image_sequence import ImageSequenceND
import pandas as pd
from pandas import DataFrame
import pickle
import os

class GUV_GUI:
    CHANNEL = 1 # channel to use for picking GUVs
    """Graphical User Interface for selecting GUVs from the microscopy data"""

    def __init__(self, stack: ImageSequenceND, guv_data: DataFrame):
        """Initialize the GUI
        
        Keyword Arguments:
            stack {ND2Stack} -- The stack to analyse (default: {None})
            series_idx {int} -- Index of the series to analyse (default: {0})
        """
        self.stack = stack
        self.stack.bundle_axes = "yx"
        self.stack.iter_axes = "z"
        self.series_idx = self.stack.default_coords['v']
        self.guv_points = dict(
            map(
                lambda f: (f,
                np.array(guv_data.loc[guv_data['frame'] == f,['x','y','r']])
                ), guv_data['frame'].unique())
            ) # make dictonairy in the form of {framenum: np.array([x1,y1,r1],[x2,y2,r2]), framenum2: np.array(...)}
        for i in range(len(stack)):
            if i not in self.guv_points:
                self.guv_points[i] = np.empty((0,3))


        self.mouseevent = {
            'press': False, 
            'start': np.empty((2,)), 
            'end': np.empty((2,)),
            'artist': None,
            }
        self.open_GUV_selector()

        # store data in .pkl file in same folder as .nd2 file
        # outfile = self.parameters['filename'].replace(".nd2","_analysis-s%02d.pkl" % self.series_idx)
        # with open(outfile,"wb") as outfile:
            # pickle.dump(self.outputdata, outfile)

    def open_GUV_selector(self):
        """Creates interface with a plot to scroll through the stack
        """
        self.root = tk.Tk()
        self.root.title("GUV selector")
        self.GUIelements = {'lblTitle': tk.Label(self.root, text='Select all GUVs')}
        self.GUIelements['lblTitle'].pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.GUIelements['lblHelp'] = tk.Label(self.root, text="Use the scroll wheel to scroll through the stack\nUse the left mouse button to select the centre of a GUV, click again to determine the radius\nand the right mouse button to remove a selected point")
        self.GUIelements['lblHelp'].pack(side=tk.TOP, fill=tk.BOTH)
        self.GUIelements['btn'] = tk.Button(self.root, text='Continue >', command=self.store_data)
        self.GUIelements['btn'].pack(side=tk.TOP, fill=tk.BOTH)
        self.window = tk.Frame(self.root)
        self.window.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.statusbar = tk.Label(self.root, text='', bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.current_frame = 0
        self.fig, self.ax = plt.subplots(1,1,figsize=(5,5),dpi=100)
        self.imax = self.ax.imshow(self.stack[self.current_frame])
        self.ax.set_title(f'frame {self.current_frame}/{len(self.stack)-1}')

        self.canvas = FigureCanvasTkAgg(self.fig, self.window)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.scrollhandler = self.canvas.mpl_connect('scroll_event', self._onscroll_guvselector) # scroll to zoom through frames
        self.presshandler = self.canvas.mpl_connect('button_press_event', self._onclick_guvselector) # click to remove points 
        self.statusbar['text'] = 'Select GUVs...'
        
        self.root.mainloop()

    def remove_all_points(self):
        """Remove all artists (selected points) from the plot, to replot them later
        """
        for a in reversed(self.ax.artists): # for some reason it only properly removes all points when reversed
            a.remove()
    
    def draw_points_on_frame(self):
        """Draws artists (selected points) for the current frame
        """
        self.remove_all_points()
        points = self.guv_points[self.current_frame]
        for point in points:
            self.ax.add_artist(matplotlib.patches.Circle(xy=point[0:2],radius=point[2],ec='r',facecolor='r',alpha=.45))
        self.canvas.draw()

    def find_closest_point_in_current_frame(self, point):
        """Find the point closest to a given coordinate

        Selects the index from self.guv_points that lies closest to
        the given coordinate
        
        Args:
            point ((x,y)): position to compare the guv_points to
        
        Returns:
            int: index of the closest point (-1 if no points were found)
        """
        points = self.guv_points[self.current_frame]
        if len(points) == 0:
            return -1
        tree = KDTree(points[:,0:2]) # only centers of circles
        return tree.query(point[0:2])[1] # index of closest point

    def _onclick_guvselector(self, event):
        """Handler for clicking the plot

        Adds artists to the current frame and removes them on right click
        
        Args:
            event (matplotlib.backend_bases.MouseEvent): Click event
        """
        coord = np.array([event.xdata, event.ydata]) # x,y coordinate of the clicked point
        
        if event.button == MouseButton.RIGHT: # remove closest point
            if self.mouseevent['press']:
                self.mouseevent['press'] = False
                [a.remove() for a in reversed(self.ax.patches)] # remove temporary circle
                self.mouseevent['artist'] = None
            else:
                idx_to_remove = self.find_closest_point_in_current_frame(np.array(coord))
                if idx_to_remove >= 0: 
                    self.guv_points[self.current_frame] = np.delete(self.guv_points[self.current_frame], idx_to_remove, axis=0)
                    self.statusbar['text'] = 'Point has been removed'
        
        self.draw_points_on_frame()

    def _onscroll_guvselector(self, event):
        """Handler for scrolling

        Increases the self.current_frame and draws all artists subsequently
        
        Args:
            event (matplotlib.backend_bases.MouseEvent): Scroll event
        """
        if event.button == 'up': # scrolling up => increase current frame
            self.current_frame = (self.current_frame +
                                  1) % len(self.stack)
        
        elif event.button == 'down': # scrolling down => decrease current frame
            self.current_frame = (self.current_frame -
                                  1) % len(self.stack)
        
        self.imax.set_data(self.stack[self.current_frame])
        self.ax.set_title(f'frame {self.current_frame}/{len(self.stack)-1} ({len(self.guv_points[self.current_frame])} GUVs)')
        self.draw_points_on_frame()
        self.canvas.draw()

    def store_data(self):
        """GUI for selecting the background box

        Removes all listeners first, then selects the frame to show (with most GUVs)
        and then initiates the GUI for selecting the background box
        """
        # guv_points_array = np.array(list(self.guv_points.values()))
        # guvs_per_frame = [guv_points_array[i].shape[0] for i in range(guv_points_array.shape[0])] 
        # nonempty_frames = [i for i in range(guv_points_array.shape[0]) if guvs_per_frame[i] > 0] 
        # self.current_frame = np.argmax(guvs_per_frame) # index of frame with highest number of GUVs

        # if len(nonempty_frames) == 0:
        #     self.statusbar['text'] = 'First select at least 1 GUV to continue...'
        #     return
        
        # self.outputdata = {
        #     'filename': os.path.basename(self.parameters['filename']),
        #     'directory': self.parameters['directory'],
        #     'series_idx': self.series_idx,
        #     'points': guv_points_array, # array with points for all frames
        #     'guvs_per_frame': guvs_per_frame, # number of GUVs per frame
        #     'nonempty_frames': nonempty_frames, # indices for frames that aren't empty
        #     'background_box': None, # to be set later
        #     'background_box_frame': self.current_frame, # frame in which the bg box was selected
        #     } # store also for later saving to file
        print("TODO: implement storing data")

        self.canvas.mpl_disconnect(self.scrollhandler)
        self.canvas.mpl_disconnect(self.presshandler)

        self.quit()

    def quit(self):
        """Destructor for the class, checks whether everyting is done first
        """
        self.root.quit()
        self.root.destroy()
    
    def get_data(self):
        """Returns the data (GUVs and background box)
        
        Returns:
            dict: Dictionairy containing information about the GUVs and background
        """
        return self.outputdata