from tkinter.filedialog import askopenfilenames
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def run():
    sns.set("paper","white")
    files = askopenfilenames(initialdir=".", title="Select files to plot...",
                                              filetypes=(("csv files", "*.csv"), ("All files", "*.*")))

    csvfiles,series = [],[]
    for f in sorted(files):
        matches = re.match(r"(.*)s(\d*).csv$", f)
        if not matches or len(matches.groups()) != 2:
            print(f"Excluding file {f} as it does not match the pattern, is it renamed?")
            continue
        csvfiles.append(f)
        series.append(int(matches.group(2)))        
    
    alldata = pd.DataFrame()
    for i,csvfile in enumerate(csvfiles):
        data = pd.read_csv(csvfile, header=0)
        data['series'] = series[i]
        alldata = alldata.append(data,ignore_index=True)
    
    sns.pairplot(alldata,vars=["r_um", "intensity", "area"],hue="series")
    plt.tight_layout()
    plt.show()

