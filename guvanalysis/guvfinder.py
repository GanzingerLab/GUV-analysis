# import necessary packages
import matplotlib as mpl
import matplotlib.pyplot as plt # for plotting
from matplotlib.patches import Circle
# mpl.rcParams['figure.dpi'] = 150
plt.rcParams['image.cmap'] = 'gray'

import numpy as np
import pandas as pd
from nd2reader import ND2Reader # for handling the nd2 file with PIMS
import pims # for loading files
from pims.image_sequence import ImageSequenceND
from PIL import Image # for image processing
from numpy.linalg import norm
from .parameters import ParameterList

from skimage.filters import gaussian
from skimage.measure import label,regionprops,regionprops_table
from skimage.feature import canny
from scipy import ndimage as ndi

class helpers:
    @staticmethod
    @pims.pipeline
    def as_8bit(frame):
        imin = frame.min()
        imax = frame.max()
        a = (255 - 0) / (imax - imin)
        b = 255 - a * imax
        return (a * frame + b).astype(np.uint8)

    @staticmethod
    @pims.pipeline
    def gaussian_5px(frame):
        return gaussian(frame, 5)

    @staticmethod
    def bounded_range(orig_range, min_val, max_val): # remove all items from a range that are outside (min,max)
        l = []
        for i in orig_range:
            if i >= min_val and i <= max_val:
                l.append(i)
        return l

    @staticmethod
    @pims.pipeline
    def process_find_edges(frame):
        return ndi.binary_fill_holes(canny(frame, sigma=1, low_threshold=20, high_threshold=50))

    @staticmethod
    def image_subregion(frame, xlims=[0,100], ylims=[0,100], circular=False):
        xmin = xlims[0] if xlims[0] >= 0 else 0
        xmax = xlims[1] if xlims[1] < frame.shape[1] else frame.shape[1]-1
        ymin = ylims[0] if ylims[0] >= 0 else 0
        ymax = ylims[1] if ylims[1] < frame.shape[0] else frame.shape[0]-1
        xmin,xmax,ymin,ymax = list(map(int, (xmin,xmax,ymin,ymax))) # convert all to integers
        newframe = frame[slice(ymin,ymax),slice(xmin,xmax)]
        if circular:
            area = newframe.size
            # assume spherical
            r = int((xmax-xmin)/2)
            for x in range(newframe.shape[1]):
                for y in range(newframe.shape[0]):
                    dx = x-r
                    dy = y-r
                    if dx**2+dy**2 > r**2:
                        newframe[y,x] = 0
                        area -= 1 # subtract area by one
            return (newframe,area) # in case of a circle return (image, circle_area(px))
        return (newframe,xmin,ymin) # in case of a square return (image,xmin,ymin)

    @staticmethod
    def scaled_GUV_intensity(frame, guv):
        x,y,r = (guv['x'],guv['y'],guv['r'])
        subregion, circle_area = helpers.image_subregion(frame, xlims=[x-r,x+r],ylims=[y-r,y+r], circular=True)
        intensity = subregion.sum()/(circle_area * np.iinfo(subregion.dtype).max) # scale by value if complete area had max intensity
        return intensity
        
    @staticmethod
    def ar(rp):
        if rp['minor_axis_length'] == 0.: # prevent division by zero
            return rp['major_axis_length']
        else:
            return rp['major_axis_length']/rp['minor_axis_length']

    @staticmethod
    def filter_GUV_dataframe(dataframe, params):
        df = dataframe[dataframe['ar'] <= params.guv_max_aspect_ratio]
        df = df[df['r'] >= params.guv_min_radius]
        return df


class GUV_finder:

    def __init__(self, stack: ImageSequenceND, parameters: ParameterList, canvas, figure):
        self.stack = stack
        self.stack.bundle_axes = 'yx' # have only yx data in one frame
        self.stack.iter_axes = 'z' # iterate over the z axis
        self.stack.default_coords['c'] = parameters.channel # select the correct channel
        if parameters.series and 'v' in self.stack.sizes:
            self.stack.default_coords['v'] = parameters.series # select the correct channel
        self.stack.default_coords['t'] = 0 # single time
        self.metadata = self.stack.metadata
        self.frames = helpers.as_8bit(stack)

        self.params = parameters

        self.guv_data = pd.DataFrame(columns=['x','y','frame','r','intensity','r_um']) # dummy data frame

        self.canvas = canvas
        self.figure = figure

    def run_analysis(self):
        self.find_GUVs_in_all_frames()
        self.link_GUV_points()
        self.get_GUVs_from_linked_points()
        self.determine_GUV_intensities()
        self.make_plots()

    def find_GUVs_in_all_frames(self):
        self.frames_filled = []
        dfcols = ('frame', 'x', 'y', 'r', 'area', 'ar')
        self.frames_regions = pd.DataFrame(columns=dfcols)
        for i,frame in enumerate(self.frames):
            self.frames_filled.append(helpers.process_find_edges(frame))
            frame_regions = regionprops_table(label(self.frames_filled[i]), properties = ('centroid', 'major_axis_length', 'minor_axis_length', 'area'))
            if frame_regions:
                # rename columns and delete old ones
                frame_regions['x'] = frame_regions['centroid-1']
                frame_regions['y'] = frame_regions['centroid-0']
                del frame_regions['centroid-0']
                del frame_regions['centroid-1']  

                # initialize dataframe for easier merging and data storage  
                frame_regions_df = pd.DataFrame(frame_regions)
                frame_regions_df['minor_axis_length'].apply(lambda x: 1. if x == 0. else x)
                frame_regions_df['ar'] = frame_regions_df['major_axis_length']/frame_regions_df['minor_axis_length']
                frame_regions_df = frame_regions_df.drop(columns = ['minor_axis_length', 'major_axis_length'])
                frame_regions_df['r'] = np.sqrt(frame_regions_df['area']/np.pi)
                frame_regions_df['frame'] = i

                # append to dataframe that holds all GUVs
                self.frames_regions = self.frames_regions.append(helpers.filter_GUV_dataframe(frame_regions_df, self.params),
                                                                 ignore_index=True)
    def link_GUV_points(self):
        points = np.array(self.frames_regions[['x','y','frame']]) # only coords
        num_points = len(points)

        # initialize arrays for storing distances in xy plane and z separately (as z corresponds to frame)
        xydistances = np.zeros(shape=(num_points,num_points))
        zdistances = np.zeros(shape=(num_points,num_points))

        for i in range(num_points-1):
            for j in range(i,num_points):
                xydist = norm(points[i,:2] - points[j,:2])
                zdist = norm(points[i,2] - points[j,2])
                xydistances[i,j] = xydist
                zdistances[i,j] = zdist

        zmask = zdistances<=self.params.track_z_thresh
        samemask = zdistances != 0.
        xymask = xydistances<=self.params.track_xy_thresh
        valid_neighbours = zmask & samemask & xymask
        pairs = np.transpose((valid_neighbours).nonzero()) # create list of pairs of indices that are neighbours
        # outputs [(1,2),(2,3),(4,5),...] for all points that are classified as neighbours on the above criterea
        
        # we need to link all points that have common neighbours
        # e.g. if 1 neighbours 2 and 2 neighbours 3, we need to make a list containing [1,2,3]
        labels = {}
        maxlabel = 0
        curlabel = False
        for i,pair in enumerate(pairs):
            for list_label,list_items in labels.items():
                if pair[0] in list_items or pair[1] in list_items: # see if either of the two indices is already present in some list
                    curlabel = list_label
                    continue # we do not need to look further once we found one occurence
            
            if curlabel is not False: # add both items to the list in which at least one was already present
                labels[curlabel].append(pair[0])
                labels[curlabel].append(pair[1])
            else: # create new list
                curlabel = maxlabel
                labels[curlabel] = list(pair)
                maxlabel = maxlabel+1

            for j in range(i,len(pairs)): # look for other occurrences with these indices in all other pairs
                if pair[0] in pairs[j] or pair[1] in pairs[j]:
                    labels[curlabel].append(pairs[j][0])
                    labels[curlabel].append(pairs[j][1])            
            
            labels[curlabel] = list(np.unique(labels[curlabel])) # remove duplicates
            curlabel = False # reset label

        # make the inverse array, e.g. {point_index: label, point2_index: label2, ...}
        inv_classifications = {}
        for classification,pointlist in labels.items():
            for p in pointlist:
                inv_classifications[p] = classification

        # add missing points
        for i in range(len(points)):
            if not i in inv_classifications:
                inv_classifications[i] = -1 # assign label -1 to all points that are on their own
        
        inv_classifications_sort = dict(sorted(inv_classifications.items())) # sort the dictonairy by key
        self.frames_regions['guv_id'] = list(inv_classifications_sort.values()) # assign the labels as 'guv_id' column

    def get_GUVs_from_linked_points(self):
        self.frames_regions['num_points'] = self.frames_regions.groupby(['guv_id'])['guv_id'].transform(len) # number of points corresponding to a certain GUV
        self.frames_regions = self.frames_regions[(self.frames_regions['num_points'] >= self.params.track_min_length) & (self.frames_regions['guv_id'] != -1)].copy()
        self.guv_data = self.frames_regions.sort_values('area', ascending=False).drop_duplicates(['guv_id']) # sort by area and use only the one with largest area

    def determine_GUV_intensities(self):
        self.stack.default_coords['c'] = self.params.intensity_channel
        intensities = []
        for _,guv in self.guv_data.iterrows():
            intensities.append(helpers.scaled_GUV_intensity(self.frames[guv['frame']], {'x': guv['x'], 'y': guv['y'], 'r': np.ceil(guv['r']).astype(int)}))
        
        self.guv_data['intensity'] = intensities

        # set channel back
        self.stack.default_coords['c'] = self.params.channel

    def make_plots(self):
        self.figure.clear()
        self.axs = self.figure.subplots(3,1)
        self.guv_data['r_um'] = self.guv_data['r']*self.metadata['pixel_microns']

        self.axs[0].scatter(self.guv_data['x'], self.guv_data['y'])
        self.axs[0].set_title("GUV positions in (x,y) plane")
        self.axs[0].set_aspect(1)
        self.axs[0].set_xlim(0,self.stack.sizes['x'])
        self.axs[0].set_ylim(self.stack.sizes['y'], 0) # images have their origin at top left

        self.axs[1].hist(self.guv_data['r_um'])
        self.axs[1].set_xlabel(r"radius (µm)")
        self.axs[1].set_title("Distribution of radii")

        self.axs[2].scatter(self.guv_data['r_um'], self.guv_data['intensity'])
        self.axs[2].set_xlabel(r"radius (µm)")
        self.axs[2].set_ylabel(r"$I/I^{max}_{sphere}$")
        self.axs[2].set_title("Radius versus intensity")

        self.figure.tight_layout(w_pad=1,h_pad=1.3)

        self.canvas.draw()

    def renew(self, guv_data):
        self.guv_data = guv_data
        self.make_plots()
    
    def get_data(self):
        return self.guv_data
