# import necessary packages
import matplotlib as mpl
import matplotlib.pyplot as plt # for plotting
from matplotlib.patches import Circle
# mpl.rcParams['figure.dpi'] = 150
plt.rcParams['image.cmap'] = 'gray'
import seaborn as sns

import numpy as np
import pandas as pd
from nd2reader import ND2Reader # for handling the nd2 file with PIMS
import pims # for loading files
from pims.image_sequence import ImageSequenceND
from PIL import Image # for image processing
from collections import namedtuple # for easier handling of parameters
# parameter_list = namedtuple("Parameters", "z_search_distance pixel_margin max_aspect_ratio min_radius") # define namedtuple for handling params

from skimage.filters import gaussian
from skimage.measure import label,regionprops
from skimage.feature import canny
from scipy import ndimage as ndi

class parameter_list(namedtuple("Parameters", "z_search_distance pixel_margin max_aspect_ratio min_radius")):
    def hello(self):
        return True

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
    #     return slice(np.min(l),np.max(l)+1)

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
        if rp['minor_axis_length'] == 0.:
            return rp['major_axis_length']
        else:
            return rp['major_axis_length']/rp['minor_axis_length']


class GUV_finder:

    def __init__(self, stack: ImageSequenceND, parameters: parameter_list, channel = 2, series_idx=None):
        self.channel = channel
        self.series_idx = series_idx
        self.stack = stack
        self.stack.bundle_axes = 'yx' # have only yx data in one frame
        self.stack.iter_axes = 'z' # iterate over the z axis
        self.stack.default_coords['c'] = channel # select the correct channel
        if series_idx and 'v' in self.stack.sizes:
            self.stack.default_coords['v'] = series_idx # select the correct channel
        self.stack.default_coords['t'] = 0 # single time
        self.metadata = self.stack.metadata
        self.frames = helpers.as_8bit(stack)

        self.params = parameters

        self.intermediates = {}
        self.find_best_frame()
        self.mean_image()
        self.determine_GUV_frame_size()
        self.determine_GUV_intensities()
        self.plot_distributions()
        self.annotate_frames()


    def find_best_frame(self):
        total_intensities = np.zeros((len(self.frames)))
        for i,f in enumerate(self.frames):
            total_intensities[i] = helpers.gaussian_5px(f).sum()
        self.best_frame = np.argmax(total_intensities[1:])+1

    def mean_image(self):
        frames_for_mean = helpers.bounded_range(range(self.best_frame-3, self.best_frame+4), 0, len(self.frames)) # make a sublist of 3 frames below and above best_frame (if possible)
        self.intermediates['mean'] = helpers.as_8bit(np.array(helpers.gaussian_5px(self.frames[frames_for_mean])).mean(axis=0)) # take the mean image of that substack
        self.intermediates['mean_filled'] = ndi.binary_fill_holes(canny(self.intermediates['mean'],sigma=3, low_threshold=20, high_threshold=50)) # do an edge detection and fill the holes 
        regions = regionprops(label(self.intermediates['mean_filled'])) # get information about the different regions in the image

        self.centroids = np.ceil(np.array(list(map(lambda x: (x.centroid[1], x.centroid[0]), regions)))).astype(np.uint) # get the centres of each of the GUVs
        self.radii = np.ceil(0.5 * np.array(list(map(lambda x: x.major_axis_length, regions)))).astype(np.uint) # and their respective radii

        fig,ax = plt.subplots(1,1)
        ax.imshow(self.intermediates['mean'])
        xs,ys = zip(*self.centroids)
        ax.scatter(xs,ys, c='r', s=3)
        plt.axis('off')
        fig.suptitle("Located centers from mean image")
        print("Centers for %d GUVs were found" % len(self.radii))
    
    def determine_GUV_frame_size(self):
        self.guv_properties = []
        for i in range(len(self.centroids)):
            x,y = self.centroids[i]
            r = self.radii[i]+self.params.pixel_margin
            frames_for_finding_maxInt = helpers.bounded_range(range(self.best_frame-self.params.z_search_distance, self.best_frame+self.params.z_search_distance+1), 0, len(self.frames))
            figw, figh = mpl.figure.figaspect(.1*len(frames_for_finding_maxInt))
            # _,ax = plt.subplots(2,len(frames_for_finding_maxInt),figsize=(figw, figh))
            local_regions = []
            for i,f in enumerate(frames_for_finding_maxInt):
                img_raw,xmin,ymin = helpers.image_subregion(self.frames[f], [x-r,x+r], [y-r,y+r])
                # ax[0,i].imshow(img_raw)
                # ax[0,i].axis('off')
                img = helpers.process_find_edges(img_raw)
                regs = regionprops(label(img))
                filtered_regs = filter(lambda x: helpers.ar(x) < self.params.max_aspect_ratio, regs) # filter regions with a too high aspect ratio 
                sorted_local_regions = sorted(filtered_regs, key = lambda i: i['area']) # sort filtered regions by decreasing area
                if sorted_local_regions: 
                    local_regions.append(sorted_local_regions[0])
                else:
                    local_regions.append({'area': 0, 'centroid': (0,0), 'major_axis_length': 0.}) # no regions found, so add empty one
                # ax[1,i].imshow(img)
                # ax[1,i].axis('off')
                # ax[1,i].set_title(r"↓")
            areas = list(map(lambda x: x['area'], local_regions))
            max_area_idx = np.argmax(areas)
            if local_regions[max_area_idx]['major_axis_length'] > self.params.min_radius:
                self.guv_properties.append({'frame': frames_for_finding_maxInt[max_area_idx],
                                    'x': np.round(local_regions[max_area_idx]['centroid'][1]+xmin).astype(int),
                                    'y': np.round(local_regions[max_area_idx]['centroid'][0]+ymin).astype(int),
                                    'area': local_regions[max_area_idx]['area'],
                                    'r': np.sqrt(local_regions[max_area_idx]['area']/np.pi), # spherical, so calculate r from area
                                    })
            # ax[0,max_area_idx].set_title('best', c='r')
            # plt.tight_layout(pad=0.0, w_pad=0.1, h_pad=0.0)

    def determine_GUV_intensities(self):
        intensity_channel = 0
        self.stack.default_coords['c'] = intensity_channel
        for guv in self.guv_properties:
            guv['intensity'] = helpers.scaled_GUV_intensity(self.frames[guv['frame']], {'x': guv['x'], 'y': guv['y'], 'r': np.ceil(guv['r']).astype(int)})

        # set channel back
        self.stack.default_coords['c'] = self.channel
        self.guv_data = pd.DataFrame(self.guv_properties)

    def plot_distributions(self):
        self.guv_data['r_um'] = self.guv_data['r']*self.metadata['pixel_microns']

        fig,ax = plt.subplots(1,3,figsize=(12,3))
        # print("Found %d GUVs with an average radius of %.02f ± %.02f µm" % )
        ax[0].hist(self.guv_data['r_um'])
        ax[0].set_title(r"$\langle r \rangle$ = %.02f ± %.02f µm [ch. #%d]" % (self.guv_data['r_um'].mean(), self.guv_data['r_um'].std(), self.channel))
        ax[0].set_xlabel(r"radius (µm)")
        ax[0].set_xlim(2.5,10.)
        # plt.savefig("histogram_radii_ch%d.png" % channel, bbox_inches='tight')

        ax[1].hist(self.guv_data['intensity'])
        ax[1].set_title(r"$\langle I/I^{max}_{sphere} \rangle$ = %.02f ± %.02f µm" % (self.guv_data['intensity'].mean(), self.guv_data['intensity'].std()))
        ax[1].set_xlabel(r"$I/I^{max}_{sphere}$")
        # ax[1].set_xlim(0.,1.)
        
        ax[2].scatter(self.guv_data['intensity'],self.guv_data['r_um'])
        ax[2].set_title(r"Intensity vs radius")
        ax[2].set_xlabel(r"$I/I^{max}_{sphere}$")
        ax[2].set_ylabel(r"radius (µm)")

        fig.suptitle(r"Distributions $(N = %d)$" % self.guv_data.shape[0])

    def annotate_frames(self):
        nonempty_frames = np.unique(list(map(lambda x: x['frame'], self.guv_properties)))
        fig,axs = plt.subplots(1,len(nonempty_frames), figsize=(5*len(nonempty_frames),5))
        for i,f in enumerate(nonempty_frames):
            guvs = list(filter(lambda x: x['frame'] == f,self.guv_properties))
            axs[i].imshow(self.frames[f])
            axs[i].set_title("%d GUVs at z=%d" % (len(guvs), f))
            axs[i].axis('off')
            for guv in guvs:
                axs[i].add_artist(Circle(xy=(guv['x'],guv['y']),radius=guv['r'],ec='r',facecolor='r',alpha=.45))
        fig.suptitle("GUVs per frame")
        plt.tight_layout(pad=0.1)
