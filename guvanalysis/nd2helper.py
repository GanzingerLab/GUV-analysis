from nd2reader import ND2Reader
from math import ceil


class ND2Stack:
    """Helper class for handling nd2 files"""

    def __init__(self, filename):
        """Initialize new nd2stack
        
        Arguments:
            filename {string} -- file name of nd2 file
        """
        self.filename = filename
        self.stack = ND2Reader(filename)
        self.stack.iter_axes = 'vz'
        self.stack.bundle_axes = 'cyx'
        self.stack.default_coords['t'] = 0
        self.num_series = self.stack.sizes['v']
        self.num_channels = self.stack.sizes['c']
        self.num_zslices = self.stack.sizes['z']
        self.series_length = self.num_zslices
        self.pixelsize = self.stack.metadata['pixel_microns']

    def print_info(self):
        """Prints a quick summary of the file"""
        print(
            "Loaded nd2 file %s.\nFile contains %d series of images.\nThe following channels are present: %s.\nEach "
            "series has %d z-slices of %dx%d pixels" %
            (self.filename, self.num_series, ", ".join(self.stack.metadata['channels']), self.num_zslices,
             self.stack.sizes['x'], self.stack.sizes['y']))

    def get_metadata(self, print_output=False):
        """Returns or prints the metadata of the file
        
        Keyword Arguments:
            print_output {bool} -- Whether or not to print the output (default: {False})

        :param print_output:  (Default value = False)
        :returns: list -- List of (key,value) pairs of the metadata

        """
        if not print_output:
            return self.stack.metadata.items()
        for k, v in self.stack.metadata.items():
            print(k, v)

    def get_series(self, series_idx):
        """Returns a sliced stack for only the certain series

        :param series_idx: int
        :param Raises: 
        :returns: ND2Reader -- sliced stack for selected series

        """
        if series_idx > self.num_series:
            raise Exception("No series with index %d exists" % series_idx)
        return self.stack[series_idx * self.series_length:(series_idx + 1) * self.series_length]

    def get_series_midframe(self, series_idx, channel_idx=1):
        """Get the frame at half z-height for given series and channel

        :param series_idx: int
        :param Keyword: Arguments
        :param channel_idx: int (Default value = 1)
        :returns: ND2Reader -- sliced stack for selected series

        """
        series = self.get_series(series_idx)
        midframe_idx = ceil(self.num_zslices / 2.)
        return series[midframe_idx][channel_idx]

    def __del__(self):
        """Close the file when the class is deleted
        """
        self.stack.close()  # close file
