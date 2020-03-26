from .nd2helper import ND2Stack
import matplotlib.pyplot as plt


class GUV_GUI:
    """Graphical User Interface for selecting GUVs from the microscopy data"""

    def __init__(self, stack: ND2Stack = None, series_idx=0):
        """Initialize the GUI
        
        Keyword Arguments:
            stack {ND2Stack} -- The stack to analyse (default: {None})
            series_idx {int} -- Index of the series to analyse (default: {0})
        """
        self.stack = stack
        self.series = stack.get_series(series_idx)
        self.open_channelscroller()

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
        self.fig.canvas.mpl_connect('scroll_event', self.onscroll)
        plt.show()

    def update(self):
        """Update the figures based on the current index"""
        for ch in range(self.stack.num_channels):
            self.imaxs[ch].set_data(
                self.series[self.current_frame][ch])
        self.fig.suptitle("Showing frame %d/%d" %
                          (self.current_frame, self.stack.series_length))
        self.fig.canvas.draw()

    def onscroll(self, event):
        """Handler for scrolling events

        :param event: matplotlib

        """
        if event.button == 'up':
            self.current_frame = (self.current_frame +
                                  1) % self.stack.series_length
        elif event.button == 'down':
            self.current_frame = (self.current_frame -
                                  1) % self.stack.series_length
        self.update()
