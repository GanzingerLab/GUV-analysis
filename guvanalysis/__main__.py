from .app import run
from .plotting import run as plot
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='python -m guvanalysis',description='GUV analysis script')    
    parser.add_argument("--show-plots", action="store_true", default=False, help="Show plots of previous analysis")
    args = parser.parse_args()
    if args.show_plots:
        plot()
    else:
        run()
