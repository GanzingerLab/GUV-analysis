from .nd2helper import ND2Stack
import tkinter as tk
import tkinter.ttk as ttk
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
import pickle
import os

class GUV_GUI:
    CHANNEL = 1 # channel to use for picking GUVs
    """Graphical User Interface for selecting GUVs from the microscopy data"""

    def __init__(self, stack: ND2Stack = None, series_idx=0, parameters = {}):
        """Initialize the GUI
        
        Keyword Arguments:
            stack {ND2Stack} -- The stack to analyse (default: {None})
            series_idx {int} -- Index of the series to analyse (default: {0})
        """
        self.stack = stack
        self.series_idx = series_idx
        self.parameters = parameters
        print(self.parameters['directory'])
        self.series = stack.get_series(series_idx)
        self.guv_points = {i: np.empty((0,3)) for i in range(self.stack.series_length)} # format self.guv_points[frame] = [[x1,y1,r1],[x2,y2,r1]]
        self.mouseevent = {
            'press': False, 
            'start': np.empty((2,)), 
            'end': np.empty((2,)),
            'artist': None,
            }
        self.open_GUV_selector()

        guv_points_array = np.array(list(self.guv_points.values()))
        guvs_per_frame = [guv_points_array[i].shape[0] for i in range(guv_points_array.shape[0])] 
        nonempty_frames = [i for i in range(guv_points_array.shape[0]) if guvs_per_frame[i] > 0] 

        outputdata = {
            'points': guv_points_array, # array with points for all frames
            'guvs_per_frame': guvs_per_frame, # number of GUVs per frame
            'nonempty_frames': nonempty_frames, # indices for frames that aren't empty
            }
        # store data in .dat file in same folder as .nd2 file
        with open(os.path.join(self.parameters['directory'],"guv_points_series-%02d.dat" % self.series_idx),"wb") as outfile:
            pickle.dump(outputdata, outfile)

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

        Will move the image viewer to the next frame

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
        lbl2 = tk.Label(self.root, text="Use the scroll wheel to scroll through the stack\nUse the left mouse button to select the centre of a GUV, click again to determine the radius\nand the right mouse button to remove a selected point")
        lbl2.pack(side=tk.TOP, fill=tk.BOTH)
        btn = tk.Button(self.root, text='Done', command=self.quit)
        btn.pack(side=tk.TOP, fill=tk.BOTH)
        self.window = tk.Frame(self.root)
        self.window.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.statusbar = tk.Label(self.root, text='', bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.current_frame = 0
        self.fig, self.ax = plt.subplots(1,1,figsize=(5,5),dpi=100)
        self.imax = self.ax.imshow(self.series[self.current_frame][self.CHANNEL])
        self.ax.set_title(f'frame {self.current_frame}/{self.stack.series_length-1}')

        self.canvas = FigureCanvasTkAgg(self.fig, self.window)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.canvas.mpl_connect('scroll_event', self._onscroll_guvselector) # scroll to zoom through frames
        self.canvas.mpl_connect('button_press_event', self._onclick_guvselector) # click to add/remove points 
        self.canvas.mpl_connect('motion_notify_event', self._onmove_guvselector) # move to update the current selection of points
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
            self.ax.add_artist(matplotlib.patches.Circle(xy=point[0:2],radius=point[2],edgecolor='r',fill=False))
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

        if event.button == MouseButton.LEFT and not self.mouseevent['press']:
            self.mouseevent['press'] = True
            self.mouseevent['start'] = coord
            self.mouseevent['artist'] = matplotlib.patches.Circle(xy=coord,radius=1.,fill=False,edgecolor='r',linestyle='--')
            self.ax.add_patch(self.mouseevent['artist'])
            self.canvas.draw()
            self.statusbar['text'] = 'Selected centre, click again to set radius of the point'
        
        elif event.button == MouseButton.LEFT and self.mouseevent['press']: # 2nd click, add point with radius to list
            self.mouseevent['end'] = coord
            radius = la.norm(self.mouseevent['end'] - self.mouseevent['start'])
            point = np.append(self.mouseevent['start'],[radius])
            self.guv_points[self.current_frame] = np.append(self.guv_points[self.current_frame], [point], axis=0)
            
            self.mouseevent['press'] = False
            [a.remove() for a in reversed(self.ax.patches)] # remove temporary circle
            self.mouseevent['artist'] = None
            self.statusbar['text'] = f'Point has been added to frame {self.current_frame}'
        
        if event.button == MouseButton.RIGHT: # remove closest point
            idx_to_remove = self.find_closest_point_in_current_frame(np.array(coord))
            if idx_to_remove >= 0: 
                self.guv_points[self.current_frame] = np.delete(self.guv_points[self.current_frame], idx_to_remove, axis=0)
                self.statusbar['text'] = 'Point has been removed'
        
        self.draw_points_on_frame()

    def _onmove_guvselector(self, event):
        """Updates the radius of the circle that is used to add a point
        
        Args:
            event (matplotlib.backend_bases.MouseEvent): Mouse move event
        """
        if not self.mouseevent['press']: # only if pressed left mouse button before
            return
        
        coord = np.array((event.xdata,event.ydata))
        radius = la.norm(coord - self.mouseevent['start'])
        self.mouseevent['artist'].set_radius(radius) # update radius of temp circle
        self.canvas.draw() # redraw the canvas to show change in radius

    def _onscroll_guvselector(self, event):
        """Handler for scrolling

        Increases the self.current_frame and draws all artists subsequently
        
        Args:
            event (matplotlib.backend_bases.MouseEvent): Scroll event
        """
        if event.button == 'up': # scrolling up => increase current frame
            self.current_frame = (self.current_frame +
                                  1) % self.stack.series_length
        
        elif event.button == 'down': # scrolling down => decrease current frame
            self.current_frame = (self.current_frame -
                                  1) % self.stack.series_length
        
        self.imax.set_data(self.series[self.current_frame][self.CHANNEL])
        self.ax.set_title(f'frame {self.current_frame}/{self.stack.series_length-1}')
        self.draw_points_on_frame()
        self.canvas.draw()
    
    def quit(self):
        """Destructor for the class
        """
        self.root.quit()
        self.root.destroy()