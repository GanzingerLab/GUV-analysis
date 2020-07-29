from dataclasses import dataclass,asdict
import json

@dataclass
class ParameterList:
    """Class to hold, load and save parameters used in the GUV tracking"""

    filename: str = "file.nd2" 
    """Name and absolute path of the .nd2 file"""

    channel: int = 2 
    """The channel that is used for determination of the positions"""

    series: int = None
    """Index of the series that should be analyzed (None for file without series)"""

    pixel_microns: float = None
    """Pixel size of the stack"""

    blur_radius: float = 1.
    """Blurring radius for the Gaussian blur that is used in the edge detection"""

    intensity_channel: int = 0
    """The channel that is used for determination of the intensity"""

    guv_max_aspect_ratio: float = 1.3
    """Maximum aspect ratio for GUVs that is considered"""

    guv_min_radius: float = 5.
    """Minimal radius (in px) that a GUV should have to be included"""
    
    track_xy_thresh: float = 7.
    """Maximal distance in xy plane (in px) for which two GUVs are considered to belong to the same track"""
    
    track_z_thresh: int = 3
    """Maximal distance in z plane (in frames) for which two GUVs are considered to belong to the same track"""

    track_min_length: int = 3
    """Minimal number of points that a track needs to have to be considered as a GUV stack"""

    def get_adjustable_variables(self):        
        vars = [
            ('blur_radius', "Blurring radius for the Gaussian blur that is used in the edge detection",(0., 10., 0.5)),
            ('guv_min_radius', "Minimal radius (in px) that a GUV should have to be included", (2., 100, 0.5)),
            ('guv_max_aspect_ratio', "Maximum aspect ratio for GUVs that is considered", (1., 5., .05)),
            ('track_xy_thresh', "Maximal distance in xy plane (in px) for which two GUVs are considered to belong to the same track", (1, 10, 1)),
            ('track_z_thresh', "Maximal distance in z plane (in frames) for which two GUVs are considered to belong to the same track", (1, 100, 1)),
            ('track_min_length', "Minimal number of points that a track needs to have to be considered as a GUV stack", (1, 100, 1)),
        ]
        output = {}
        for varname, helptext, limits in vars:
            output[varname] = {
                'value': getattr(self,varname),
                'helptext': helptext,
                'min': limits[0],
                'max': limits[1],
                'step': limits[2],
            }
        return output


    def to_json(self, filename):
        """Write the current parameters to a .json file"""

        with open(filename,"w") as jsonfile:
            json.dump(asdict(self), jsonfile, indent=4)

    @staticmethod
    def from_json(filename):
        """Load parameters from a json file"""

        with open(filename,"r") as jsonfile:
            data = json.load(jsonfile)
        return ParameterList(**data)

