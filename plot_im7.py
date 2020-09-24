import IM
import os.path
import matplotlib.pyplot as plt
import numpy as np

filename = "B00050.im7"
pathBefore = "./testdata"
pathAfter = "./testdata/SubOverTimeMin_sL=20"

before = IM.IM7(os.path.join(os.path.abspath(pathBefore), filename))
after = IM.IM7(os.path.join(os.path.abspath(pathAfter), filename))

frame = 0
fig, ax = plt.subplots(ncols=2, dpi=100, figsize=(10, 4))
data = before.maI.data[frame, :, :]
plot1 = ax[0].imshow(data, extent=before.extent, cmap="jet", vmin=0, vmax=np.quantile(data, 0.99))
clim = plot1.get_clim()
ax[0].set_title("Original Image")
ax[0].set_xlabel("x")
ax[0].set_ylabel("y")

plot2 = ax[1].imshow(after.maI.data[frame, :, :], extent=after.extent, cmap="jet")
plot2.set_clim(clim)
plt.title("After Time Subtraction")
ax[1].set_xlabel("x")
ax[1].set_ylabel("y")
