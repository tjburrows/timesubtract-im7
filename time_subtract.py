import glob
import os
from im7_class import IM7
import dask
import dask.array as da
from dask_image.ndfilters import minimum_filter
import numpy as np
from dask.distributed import Client, LocalCluster

# Path to IM7 files
im7_path = './testdata'

# Path for temporary files
temp_path = './temp'

# Filter length
n = 5

# Number of workers
workers = 4

# Memory limit per worker
worker_mem = '2GB'

def cleanup(environment):
    if 'client' in environment:
        client.close()
    if 'cluster' in environment:
        cluster.close()

def writeIM7(Idata, im7, newPath):
        im7.data['I'] = np.ma.masked_array(Idata.astype(sampleDtype), mask=im7.data['I'].mask)
        im7.writeIM7(newPath)

if __name__ == '__main__':    
    cleanup(dir())
    
    cluster = LocalCluster(n_workers=workers, memory_limit=worker_mem, processes=True, dashboard_address='127.0.0.1:8787', local_directory=temp_path)
    client = Client(cluster)
    print(client)
    
    im7_path = os.path.abspath(im7_path)
    filenames = glob.glob(os.path.join(im7_path, '*.im7'))
    filenames = list(map(os.path.abspath, filenames))
    
    if not filenames:
        raise ValueError('No .im7 files found at %s' % im7_path)
        
    filenamesOnly = list(map(os.path.basename, filenames))
    numImages = len(filenames)
    l = (n - 1) / 2
    sample1 = IM7(filenames[0])
    sampleShape = sample1.data['I'].data.shape
    sampleDtype = sample1.data['I'].data.dtype
    lazy_im7s = [dask.delayed(IM7)(file) for file in filenames]
    lazy_arrays = [da.from_delayed(im7.data['I'].data, shape=sampleShape, dtype=sampleDtype) for im7 in lazy_im7s]
    lazyStack = da.stack(lazy_arrays)
    lazyStack = lazyStack.rechunk('auto')
    
    # Find minimum of n points along first axis
    slidingMinShape = (n, 1, 1, 1)
    minimum = minimum_filter(lazyStack, size=slidingMinShape, mode='nearest')
    newImages = lazyStack - minimum
    
    folder = 'SubOverTimeMin_sL=%d' % n
    folder = os.path.join(im7_path, folder)
    if not os.path.exists(folder):
        os.mkdir(folder)
    
    
    writes = []
    for i in range(0, lazyStack.shape[0]):
        newPath = os.path.join(im7_path, folder, filenamesOnly[i])
        writes.append(dask.delayed(writeIM7)(newImages[i,:], lazy_im7s[i], newPath))

    try:
        dask.compute(*writes)
        cleanup(dir())
    except:
        cleanup(dir())
