import glob
import os
from im7_class import IM7
import dask
import dask.array as da
from dask_image.ndfilters import minimum_filter
import numpy as np
from dask.distributed import Client, LocalCluster

# Path to IM7 files
im7_path = "./testdata"

# Path for temporary files
temp_path = "./temp"

# Filter length
n = 5

# Number of workers
workers = 4

# Memory limit per worker
worker_mem = "2GB"

# Terminates dask client / cluster
def cleanup(environment):
    if "client" in environment:
        client.close()
    if "cluster" in environment:
        cluster.close()


# Write IM7 object with new image data
def writeIM7(Idata, oldIM7, newPath):
    oldIM7.data["I"] = np.ma.masked_array(Idata.astype(sampleDtype), mask=oldIM7.data["I"].mask)
    oldIM7.writeIM7(newPath)


if __name__ == "__main__":
    cleanup(dir())

    # Initialize Dask
    cluster = LocalCluster(
        n_workers=workers,
        memory_limit=worker_mem,
        processes=True,
        dashboard_address="127.0.0.1:8787",
        local_directory=temp_path,
    )
    client = Client(cluster)
    print(client)

    # Find IM7 files
    im7_path = os.path.abspath(im7_path)
    filenames = glob.glob(os.path.join(im7_path, "*.im7"))
    filenames = list(map(os.path.abspath, filenames))
    if not filenames:
        raise ValueError("No .im7 files found at %s" % im7_path)
    filenamesOnly = list(map(os.path.basename, filenames))
    numImages = len(filenames)

    # Length of one side of filter
    l = (n - 1) / 2

    # Load one image to get data shape and type
    sample1 = IM7(filenames[0])
    sampleShape = sample1.data["I"].data.shape
    sampleDtype = sample1.data["I"].data.dtype

    # Lazy load IM7 files and convert to 3D array, 1st dimension time
    lazy_im7s = [dask.delayed(IM7)(file) for file in filenames]
    lazy_arrays = [
        da.from_delayed(im7.data["I"].data, shape=sampleShape, dtype=sampleDtype)
        for im7 in lazy_im7s
    ]
    lazyStack = da.stack(lazy_arrays)
    lazyStack = lazyStack.rechunk("auto")

    # Find minimum of n points along first axis
    slidingMinShape = (n, 1, 1, 1)
    minimum = minimum_filter(lazyStack, size=slidingMinShape, mode="nearest")
    newImages = lazyStack - minimum

    # Create folder with Davis name convention
    folder = "SubOverTimeMin_sL=%d" % n
    folder = os.path.join(im7_path, folder)
    if not os.path.exists(folder):
        os.mkdir(folder)

    # Create list of operations
    writes = []
    for i in range(0, lazyStack.shape[0]):
        newPath = os.path.join(im7_path, folder, filenamesOnly[i])
        writes.append(dask.delayed(writeIM7)(newImages[i, :], lazy_im7s[i], newPath))

    # Execute operations
    try:
        dask.compute(*writes)
        cleanup(dir())
    except:
        cleanup(dir())
