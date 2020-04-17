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
import pickle
import os

class GUV_GUI:
    CHANNEL = 1 # channel to use for picking GUVs
    """Graphical User Interface for selecting GUVs from the microscopy data"""

    def __init__(self, stack: ND2Reader = None, parameters = {}):
        """Initialize the GUI
        
        Keyword Arguments:
            stack {ND2Stack} -- The stack to analyse (default: {None})
            series_idx {int} -- Index of the series to analyse (default: {0})
        """
        self.stack = stack
        self.series_idx = self.stack.default_coords['v']
        self.parameters = parameters
        self.guv_points = {i: np.empty((0,3)) for i in range(len(self.stack))} # format self.guv_points[frame] = [[x1,y1,r1],[x2,y2,r1]]
        self.mouseevent = {
            'press': False, 
            'start': np.empty((2,)), 
            'end': np.empty((2,)),
            'artist': None,
            }
        self.open_GUV_selector()

        # store data in .pkl file in same folder as .nd2 file
        outfile = self.parameters['filename'].replace(".nd2","_analysis-s%02d.pkl" % self.series_idx)
        with open(outfile,"wb") as outfile:
            pickle.dump(self.outputdata, outfile)

    def open_GUV_selector(self):
        """Creates interface with a plot to scroll through the stack
        """
        self.root = tk.Tk()
        self.root.title("GUV selector")
        self.GUIelements = {'lblTitle': tk.Label(self.root, text='Select all GUVs')}
        self.GUIelements['lblTitle'].pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.GUIelements['lblHelp'] = tk.Label(self.root, text="Use the scroll wheel to scroll through the stack\nUse the left mouse button to select the centre of a GUV, click again to determine the radius\nand the right mouse button to remove a selected point")
        self.GUIelements['lblHelp'].pack(side=tk.TOP, fill=tk.BOTH)
        self.GUIelements['btn'] = tk.Button(self.root, text='Continue to background selection >', command=self.open_BG_selector)
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
        self.presshandler = self.canvas.mpl_connect('button_press_event', self._onclick_guvselector) # click to add/remove points 
        self.movehandler = self.canvas.mpl_connect('motion_notify_event', self._onmove_guvselector) # move to update the current selection of points
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
                                  1) % len(self.stack)
        
        elif event.button == 'down': # scrolling down => decrease current frame
            self.current_frame = (self.current_frame -
                                  1) % len(self.stack)
        
        self.imax.set_data(self.stack[self.current_frame])
        self.ax.set_title(f'frame {self.current_frame}/{len(self.stack)-1}')
        self.draw_points_on_frame()
        self.canvas.draw()

    def open_BG_selector(self):
        """GUI for selecting the background box

        Removes all listeners first, then selects the frame to show (with most GUVs)
        and then initiates the GUI for selecting the background box
        """
        guv_points_array = np.array(list(self.guv_points.values()))
        guvs_per_frame = [guv_points_array[i].shape[0] for i in range(guv_points_array.shape[0])] 
        nonempty_frames = [i for i in range(guv_points_array.shape[0]) if guvs_per_frame[i] > 0] 
        self.current_frame = np.argmax(guvs_per_frame) # index of frame with highest number of GUVs

        if len(nonempty_frames) == 0:
            self.statusbar['text'] = 'First select at least 1 GUV to continue...'
            return
        
        self.outputdata = {
            'filename': os.path.basename(self.parameters['filename']),
            'directory': self.parameters['directory'],
            'series_idx': self.series_idx,
            'points': guv_points_array, # array with points for all frames
            'guvs_per_frame': guvs_per_frame, # number of GUVs per frame
            'nonempty_frames': nonempty_frames, # indices for frames that aren't empty
            'background_box': None, # to be set later
            'background_box_frame': self.current_frame, # frame in which the bg box was selected
            } # store also for later saving to file
        
        self.canvas.mpl_disconnect(self.scrollhandler)
        self.canvas.mpl_disconnect(self.presshandler)
        self.canvas.mpl_disconnect(self.movehandler)

        self.imax.set_data(self.stack[self.current_frame])
        self.ax.set_title(f'frame {self.current_frame}/{len(self.stack)-1}')
        self.draw_points_on_frame()
        self.canvas.draw()
        self.GUIelements['lblTitle']['text'] = 'Select box with background'
        self.GUIelements['lblHelp']['text'] = 'Click somewhere with the left mousebutton to select the first corner of the box\nthen move and press again to select the second corner\nUse right mouse button to undo'
        self.GUIelements['btn']['command'] = self.quit
        self.GUIelements['btn']['text'] = "Done"
        self.statusbar['text'] = "Select first point of background box"
        self.presshandler = self.canvas.mpl_connect('button_press_event', self._onclick_bgselector) # click to add/remove points 
        self.movehandler = self.canvas.mpl_connect('motion_notify_event', self._onmove_bgselector) # move to update the current selection of points

    def remove_bgbox(self):
        self.outputdata['background_box'] = None
        self.mouseevent['press'] = False
        [a.remove() for a in reversed(self.ax.patches)] # remove temporary circle
        self.mouseevent['artist'] = None
        self.canvas.draw()

    def _onclick_bgselector(self, event):
        """Handler for clicking the plot, handles drawing the background box
        
        Args:
            event (matplotlib.backend_bases.MouseEvent): Click event
        """
        coord = np.array([event.xdata, event.ydata]) # x,y coordinate of the clicked point

        if event.button == MouseButton.LEFT and not self.mouseevent['press']:
            self.remove_bgbox()
            self.mouseevent['press'] = True
            self.mouseevent['start'] = coord
            self.mouseevent['artist'] = matplotlib.patches.Rectangle(xy=coord,width=1.,height=1.,fill=False,edgecolor='r',linestyle='--')
            self.ax.add_patch(self.mouseevent['artist'])
            self.statusbar['text'] = 'Selected first corner, click again to set second corner'
        
        elif event.button == MouseButton.LEFT and self.mouseevent['press']: # 2nd click, set 2nd point of box and store
            self.mouseevent['end'] = coord
            self.outputdata['background_box'] = np.append([self.mouseevent['start']],[coord]) # format (x1,y1,x2,y2)
            
            self.mouseevent['press'] = False
            self.statusbar['text'] = f'Background box has been drawn, click button on top to continue...'
        
        if event.button == MouseButton.RIGHT: # remove closest point
            self.remove_bgbox()
            self.statusbar['text'] = 'Background box has been removed'

        self.canvas.draw()

    def _onmove_bgselector(self, event):
        """Updates the box for background selection
        
        Args:
            event (matplotlib.backend_bases.MouseEvent): Mouse move event
        """
        if not self.mouseevent['press']: # only if pressed left mouse button before
            return
        
        coord = np.array((event.xdata,event.ydata))
        distance = coord-self.mouseevent['start']
        self.mouseevent['artist'].set_width(distance[0]) 
        self.mouseevent['artist'].set_height(distance[1]) 
        self.canvas.draw() # redraw the canvas to show change in radius
    
    def quit(self):
        """Destructor for the class, checks whether everyting is done first
        """
        if self.outputdata['background_box'] is None:
            self.statusbar['text'] = "Can't proceed without selecting background"
            return
        self.root.quit()
        self.root.destroy()
    
    def get_data(self):
        """Returns the data (GUVs and background box)
        
        Returns:
            dict: Dictionairy containing information about the GUVs and background
        """
        return self.outputdata