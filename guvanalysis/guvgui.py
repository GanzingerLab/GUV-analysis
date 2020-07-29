import tkinter as tk
import tkinter.ttk as ttk
from nd2reader.reader import ND2Reader
import numpy as np
import numpy.linalg as la
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
plt.rcParams['image.cmap'] = 'gray'
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
    """Graphical User Interface for selecting GUVs from the microscopy data"""

    def __init__(self, stack: ImageSequenceND, guv_data: DataFrame, canvas: FigureCanvasTkAgg, figure: Figure, updateddata_callback = None):
        """Initialize the GUI
        
        Keyword Arguments:
            stack {ImageSequenceND}: The stack to analyse
            guv_data {pd.DataFrame}: DataFrame containing the positions (x,y) and radii (r) of the GUVs
            canvas {FigureCanvasTkAgg}: The canvas used to plot
            figure {Figure}: The figure object used to plot
        """
        self.stack = stack
        # self.stack.bundle_axes = "yx"
        # self.stack.iter_axes = "z" # iterate over only z axis, channel should be set in app.py
        self.guv_data = guv_data

        self.canvas = canvas
        self.fig = figure

        self.updateddata_callback = updateddata_callback # function to call if data is updated by user
        
        self.current_frame = 0

        self.open_GUV_selector() # launch the GUI

    def renew(self, guv_data):
        self.guv_data = guv_data
        self.open_GUV_selector()
        self.draw_points_on_frame()


    def open_GUV_selector(self):
        """Creates interface with a plot to scroll through the stack
        """
        # self.fig = figure
        # plt.figure will block the tkinter mainloop and prevent the program from exiting: https://stackoverflow.com/a/17535868
        self.make_current_frame_points_array()
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_axis_off()
        self.imax = self.ax.imshow(self.stack[self.current_frame])
        self.ax.set_title(f'frame {self.current_frame}/{len(self.stack)-1}  ({len(self.guv_points)} GUVs)')
        
        plt.tight_layout()

        self.scrollhandler = self.canvas.mpl_connect('scroll_event', self._onscroll_guvselector) # scroll to zoom through frames
        self.scrollhandler = self.canvas.mpl_connect('key_press_event', self._onscroll_guvselector) # key up/down to zoom through frames
        self.presshandler = self.canvas.mpl_connect('button_press_event', self._onclick_guvselector) # click to remove points 
        
        # self.root.mainloop()

    def remove_all_points(self):
        """Remove all artists (selected points) from the plot, to replot them later
        """
        for a in reversed(self.ax.artists): # for some reason it only properly removes all points when reversed
            a.remove()
    
    def make_current_frame_points_array(self):
        """Makes an array with points for the current shown frame

        Only the x,y,r variables are selected from the dataframe and converted to 
        a numpy array
        """
        subdf = self.guv_data.loc[self.guv_data['frame'] == self.current_frame,['x','y','r']]
        if subdf.empty:
            self.guv_points = np.empty(shape=(0,3))
            return
        self.guv_points = np.array(subdf)

    def draw_points_on_frame(self):
        """Draws artists (selected points) for the current frame
        """
        self.remove_all_points()
        
        for _,point in self.guv_data.iterrows():
            c,a = ('yellow', .45) if point['frame'] == self.current_frame else ('blue', .25)
            # red if in current frame, blue if in other frame, also adjust transparency for clarity
            self.ax.add_artist(matplotlib.patches.Circle(xy=(point['x'],point['y']),radius=point['r'],ec=c,facecolor=c,alpha=a))
        
        self.canvas.draw()

    def find_closest_point_in_current_frame(self, point):
        """Find the point closest to a given coordinate

        Selects the index from self.guv_data that lies closest to
        the given coordinate
        
        Args:
            point ((x,y)): position to compare the guv_points to
        
        Returns:
            int: index of the closest point (-1 if no points were found)
        """
        if len(self.guv_points) == 0:
            return -1
        tree = KDTree(self.guv_points[:,0:2]) # only centers of circles
        array_idx = tree.query(point[0:2])[1] # index of closest point within array
        # convert the array index to the index of the row in the dataframe
        return self.guv_data.index[self.guv_data['frame'] == self.current_frame][array_idx]

    def _onclick_guvselector(self, event):
        """Handler for clicking the plot

        Adds artists to the current frame and removes them on right click
        
        Args:
            event (matplotlib.backend_bases.MouseEvent): Click event
        """
        coord = np.array([event.xdata, event.ydata]) # x,y coordinate of the clicked point
        
        if event.button == MouseButton.RIGHT: # remove closest point
            idx_to_remove = self.find_closest_point_in_current_frame(np.array(coord))
            if idx_to_remove >= 0:                     
                self.guv_data = self.guv_data.drop(idx_to_remove)
                self.make_current_frame_points_array()
                if self.updateddata_callback is not None:
                    self.updateddata_callback()
        
        self.draw_points_on_frame()

    def _onscroll_guvselector(self, event):
        """Handler for scrolling

        Increases the self.current_frame and draws all artists subsequently
        
        Args:
            event (matplotlib.backend_bases.MouseEvent): Scroll event
        """
        if event.button == 'up' or event.key == 'up': # scrolling up => increase current frame
            self.current_frame = (self.current_frame +
                                  1) % len(self.stack)
        
        elif event.button == 'down' or event.key == 'down': # scrolling down => decrease current frame
            self.current_frame = (self.current_frame -
                                  1) % len(self.stack)
        
        self.imax.set_data(self.stack[self.current_frame])        
        self.make_current_frame_points_array()
        self.ax.set_title(f'frame {self.current_frame}/{len(self.stack)-1} ({len(self.guv_points)} GUVs)')
        self.draw_points_on_frame()
        self.canvas.draw()

    def store_data(self, filename):
        """GUI for selecting the background box

        Stores the correct dataframe as csv file to given location
        and quit the program

        Args:
            filename (str): Filename of the csv file in which the data is stored
        """
        self.guv_data.to_csv(filename, index=False, header=True)

        self.quit()


    def quit(self):
        """Destructor for the class, removes listeners and closes windows
        """
        self.canvas.mpl_disconnect(self.scrollhandler)
        self.canvas.mpl_disconnect(self.presshandler)
        # self.root.quit()
    
    def get_data(self):
        """Returns the data
        
        Returns:
            pd.DataFrame: Dataframe with information about sizes and positions of GUVs
        """
        return self.guv_data