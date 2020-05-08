import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from glob import glob
import re

sns.set("paper","whitegrid")

# filename = r"C:\Users\Roy\Documents\AMOLF\GUV-analysis\galvano_003_10series.nd2"
filename = input("Give the name (path) of the file:\n")
pattern = filename.replace(".nd2","")+"_GUVdata-s*.csv"

csvfiles = [f for f in glob(pattern)]
# print(csvfiles)

series = list(map(lambda x: int(re.match(r"(.*)s(\d*).csv$", x).group(2)), csvfiles))

alldata = pd.DataFrame()
for i,csvfile in enumerate(csvfiles):
    data = pd.read_csv(csvfile, header=0)
    data['series'] = series[i]
    alldata = alldata.append(data,ignore_index=True)

sns.pairplot(alldata,vars=["r_um", "intensity", "area"],hue="series")
plt.tight_layout()
plt.show()