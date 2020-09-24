# timesubtract-im7
Python script which implements a parallelized rolling minimum time subtraction filter for a time series of LaVision Davis IM7 files (particle image velocimetry).

![before-after plot](/before-after.png)

## Introduction
The [LaVision Davis](https://www.lavision.de/en/products/davis-software) software has time subtraction built in, but it is limited to local processing on a Windows workstation.  This implementation performs the same operation using Python and [Dask](https://dask.org), allowing for local and cluster computing on any operating system.  This serves as an example of IM7 parallel processing that could be a starting point for creating a suite of parallelized image processing operations.

## Features
 - Adjustable filter length *n*
 - Control of worker number and memory usage
 - Tested on planar and stereo images, should also work on tomographic
 - Implemented for a [single machine](https://docs.dask.org/en/latest/setup/single-distributed.html) but is [easily adapted](https://docs.dask.org/en/latest/setup.html) to run on a Dask-compatible cluster
 
## Requirements
### time_subtract.py
Install the below requirements with `pip install requirements.txt`
- Numpy
- Dask
- Dask-image
- [ReadIM](https://bitbucket.org/fleming79/readim)

### plot_im7.py
This requires matplotlib, numpy, and [IM](https://bitbucket.org/fleming79/im).  Install IM with `pip install git+https://bitbucket.org/fleming79/im`


## Usage
### time_subtract.py
This is the main script that performs the time subtraction.  Relevent parameters are commented and are below.  To run, use the command `python time_subtract.py`.  Because of the parallization, this script cannot be run in Spyder.
 - *im7_path*: path to IM7 files
 - *temp_path*: path for temporary Dask files
 - *n*: filter length
 - *workers*: number of parallel workers
 - *worker_mem*: amount of memery to use per worker

### plot_im7.py
This script plots a before and after image for a given time subtraction.  Path and file names must be changed for this to work.  An example output plot from this script is shown above.
