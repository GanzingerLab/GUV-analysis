from nd2reader import ND2Reader

class nd2stack:
    def __init__(self, filename):
        """Initialize new nd2stack
        
        Arguments:
            filename {string} -- file name of nd2 file
        """
        self.filename = filename
        self.stack = ND2Reader(filename)
        self.stack.iter_axes = 'vz'
        self.stack.bundle_axes = 'cyx'
        self.num_series = self.stack.sizes['v']
        self.num_channels = self.stack.sizes['c']
        self.num_zslices = self.stack.sizes['z']
        self.series_length = self.num_zslices

    def print_info(self):
        """Prints a quick summary of the file
        """
        print("Loaded nd2 file %s.\nFile contains %d series of images.\nThe following channels are present: %s.\nEach serie has %d z-slices of %dx%d pixels" %
              (self.filename, self.num_series, ", ".join(self.stack.metadata['channels']), self.num_zslices, self.stack.sizes['x'], self.stack.sizes['y']))

    def print_metadata(self):
        """Prints the metadata of the file
        """
        for k, v in self.stack.metadata.items():
            print(k, v)

    def get_series(self, series_idx):
        """Returns a sliced stack for only the certain series
        
        Arguments:
            series_idx {int} -- index of the series
        
        Raises:
            Exception: Thrown when the index is larger than the number of series
        
        Returns:
            ND2Reader -- sliced stack for selected series
        """
        if series_idx > self.num_series:
            raise Exception("No series with index %d exists" % series_idx)
        return self.stack[series_idx*self.series_length:(series_idx+1)*self.series_length]

    def __del__(self):
        """Close the file when the class is deleted
        """
        self.stack.close()  # close file
