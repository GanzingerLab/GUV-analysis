from .nd2helper import ND2Stack
import tkinter as tk
import tkinter.ttk as ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches
from matplotlib.backend_bases import MouseEvent,MouseButton
from scipy.spatial import KDTree

class GUV_GUI:
    CHANNEL = -1 # channel to use for picking GUVs
    """Graphical User Interface for selecting GUVs from the microscopy data"""

    def __init__(self, stack: ND2Stack = None, series_idx=0):
        """Initialize the GUI
        
        Keyword Arguments:
            stack {ND2Stack} -- The stack to analyse (default: {None})
            series_idx {int} -- Index of the series to analyse (default: {0})
        """
        self.stack = stack
        self.series_idx = series_idx
        self.series = stack.get_series(series_idx)
        self.guv_points = {i: np.empty((0,2)) for i in range(self.stack.series_length)} # format self.guv_points[frame] = [[x1,y1],[x2,y2]]
        # self.open_channelscroller()
        self.open_GUV_selector()

    def open_channelscroller(self):
        """Display matplotlib figure of all channels next to each other through which the user can scroll"""
        self.current_frame = 0
        self.fig, self.axs = plt.subplots(1, self.stack.num_channels, figsize=(12, 5))
        self.fig.suptitle("Showing frame %d/%d" %
                          (self.current_frame, self.stack.series_length))
        self.imaxs = []
        for ch in range(self.stack.num_channels):
            self.imaxs.append(self.axs[ch].imshow(
                self.series[self.current_frame][ch]))
            self.axs[ch].set_title("channel %d\n%s" % (ch, self.stack.stack.metadata['channels'][ch]))
        self.fig.canvas.mpl_connect('scroll_event', self._onscroll_channelscroller)
        plt.show()

    def _update_channelscroller(self):
        """Update the figures based on the current index"""
        for ch in range(self.stack.num_channels):
            self.imaxs[ch].set_data(
                self.series[self.current_frame][ch])
        self.fig.suptitle("Showing frame %d/%d" %
                          (self.current_frame, self.stack.series_length))
        self.fig.canvas.draw()

    def _onscroll_channelscroller(self, event):
        """Handler for scrolling events

        :param event: matplotlib

        """
        if event.button == 'up':
            self.current_frame = (self.current_frame +
                                  1) % self.stack.series_length
        elif event.button == 'down':
            self.current_frame = (self.current_frame -
                                  1) % self.stack.series_length
        self._update_channelscroller()

    def open_GUV_selector(self):
        """Creates interface with a plot to scroll through the stack
        """
        self.root = tk.Tk()
        self.root.title("GUV selector")
        lbl = tk.Label(self.root, text='Select all GUVs')
        lbl.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        lbl2 = tk.Label(self.root, text="Use the scroll wheel to scroll through the stack\nUse the left mouse button to select a GUV and the right mouse button to remove a selected point")
        lbl2.pack(side=tk.TOP, fill=tk.BOTH)
        self.window = tk.Frame(self.root)
        self.window.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.current_frame = 0
        self.fig, self.ax = plt.subplots(1,1,figsize=(5,5),dpi=150)
        self.imax = self.ax.imshow(self.series[self.current_frame][self.CHANNEL])
        self.ax.set_title(f'frame {self.current_frame}/{self.stack.series_length-1}')

        self.canvas = FigureCanvasTkAgg(self.fig, self.window)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.canvas.mpl_connect('scroll_event', self._onscroll_guvselector)
        self.canvas.mpl_connect('button_press_event', self._onclick_guvselector)
        self.root.mainloop()

    def remove_all_points(self):
        """Remove all artists (selected points) from the plot
        """
        for a in reversed(self.ax.artists): # for some reason it only properly removes all points when reversed
            a.remove()
    
    def draw_points_on_frame(self):
        """Draws artists (selected points) for the current frame
        """
        self.remove_all_points()
        points = self.guv_points[self.current_frame]
        for point in points:
            self.ax.add_artist(matplotlib.patches.Ellipse(xy=point,width=10.,height=10.,facecolor='r'))
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
        tree = KDTree(points)
        return tree.query(point)[1] # index of closest point

    def _onclick_guvselector(self, event):
        """Handler for clicking the plot

        Adds artists to the current frame and removes them on right click
        
        Args:
            event (matplotlib.backend_bases.MouseEvent): Click event
        """
        if event.button == MouseButton.LEFT:
            self.guv_points[self.current_frame] = np.append(self.guv_points[self.current_frame], [[event.xdata, event.ydata]], axis=0)
        if event.button == MouseButton.RIGHT: # remove closest point
            idx_to_remove = self.find_closest_point_in_current_frame(np.array([event.xdata,event.ydata]))
            if idx_to_remove >= 0:
                self.guv_points[self.current_frame] = np.delete(self.guv_points[self.current_frame], idx_to_remove, axis=0)
        self.draw_points_on_frame()

    def _onscroll_guvselector(self, event):
        """Handler for scrolling

        Increases the self.current_frame and draws all artists subsequently
        
        Args:
            event (matplotlib.backend_bases.MouseEvent): Scroll event
        """
        if event.button == 'up':
            self.current_frame = (self.current_frame +
                                  1) % self.stack.series_length
        elif event.button == 'down':
            self.current_frame = (self.current_frame -
                                  1) % self.stack.series_length
        
        self.imax.set_data(self.series[self.current_frame][self.CHANNEL])
        self.ax.set_title(f'frame {self.current_frame}/{self.stack.series_length-1}')
        self.draw_points_on_frame()
        self.canvas.draw()
    
    def __del__(self):
        """Destructor for the class
        """
        self.root.quit()
        self.root.destroy()