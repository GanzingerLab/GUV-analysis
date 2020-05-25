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

    intensity_channel: int = 0
    """The channel that is used for determination of the intensity"""

    guv_max_aspect_ratio: float = 1.3
    """Maximum aspect ratio for GUVs that is considered"""

    guv_min_radius: float = 7.
    """Minimal radius (in px) that a GUV should have to be included"""
    
    track_xy_thresh: float = 7.
    """Maximal distance in xy plane (in px) for which two GUVs are considered to belong to the same track"""
    
    track_z_thresh: int = 2
    """Maximal distance in z plane (in frames) for which two GUVs are considered to belong to the same track"""

    track_min_length: int = 3
    """Minimal number of points that a track needs to have to be considered as a GUV stack"""

    def get_adjustable_variables(self):        
        vars = [
            ('guv_min_radius', (2., 100, 0.5)),
            ('guv_max_aspect_ratio', (1., 5., .1)),
            ('track_xy_thresh', (1, 10, 1)),
            ('track_z_thresh', (1, 100, 1)),
            ('track_min_length', (1, 100, 1)),
        ]
        output = {}
        for varname, limits in vars:
            output[varname] = {
                'value': getattr(self,varname),
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

