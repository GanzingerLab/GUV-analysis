from dataclasses import dataclass,asdict
import json

@dataclass
class ParameterList:
    """Class to hold, load and save parameters used in the GUV tracking"""

    channel: int = 2 
    """The channel that is used for determination of the positions"""

    series: int = None
    """Index of the series that should be analyzed (None for file without series)"""

    intensity_channel: int = 0
    """The channel that is used for determination of the intensity"""

    max_aspect_ratio: float = 1.3
    """Maximum aspect ratio for GUVs that is considered"""

    min_radius: float = 7.
    """Minimal radius (in px) that a GUV should have to be included"""
    
    pixel_margin: int = 15
    """Margin that the radius of a GUV is grown when looking in adjacent frames"""

    z_search_distance: int = 7
    """Number of frames in z direction to look for bigger GUV area"""

    def to_json(self, filename):
        """Write the current parameters to a .json file"""

        with open(filename,"w") as jsonfile:
            json.dump(asdict(self), jsonfile)

    @staticmethod
    def from_json(filename):
        """Load parameters from a json file"""

        with open(filename,"r") as jsonfile:
            data = json.load(jsonfile)
        return ParameterList(**data)

