#!/usr/bin/env python
u"""
calc_sensitivity_kernel.py
Written by Tyler Sutterley (01/2021)

Calculates spatial sensitivity kernels through a least-squares mascon procedure

CALLING SEQUENCE:
    python calc_sensitivity_kernel.py mascon_parameter_file

    Can also input several parameter files in series:
    python calc_sensitivity_kernel.py parameter_file1 parameter_file2

    Can be run in parallel with the python multiprocessing package:
    python calc_sensitivity_kernel.py --np=2 parameter_file1 parameter_file2
    python calc_sensitivity_kernel.py -P 2 parameter_file1 parameter_file2

    Can output a log file listing the input parameters and output files:
    python calc_sensitivity_kernel.py --log parameter_file
    python calc_sensitivity_kernel.py -l parameter_file

SYSTEM ARGUMENTS README:
    program is run as:
    python calc_sensitivity_kernel.py inp1 inp2 inp3
        where inp1, inp2 and inp3 are different inputs

        firstinput=sys.argv[1] (in this case inp1)
        secondinput=sys.argv[2] (in this case inp2)
        thirdinput=sys.argv[3] (in this case inp3)

    As python is base 0, sys.argv[0] is equal to calc_sensitivity_kernel.py
        (which is useful in some applications, but not for this program)

    For this program, the system arguments are parameter files
    The program reads the parameter file, which is separated by column as:
        Column 1: parameter name (such as LMAX)
        Column 2: parameter (e.g. 60)
        Column 3: comments (which are discarded)
    The parameters are stored in a python dictionary (variables indexed by keys)
        the keys are the parameter name (for LMAX: parameters['LMAX'] == 60)

INPUTS:
    parameter files containing specific variables for each analysis

COMMAND LINE OPTIONS:
    --help: list the command line options
    -P X, --np X: Run in parallel with X number of processes
    -n X, --love X: Load Love numbers dataset
        0: Han and Wahr (1995) values from PREM
        1: Gegout (2005) values from PREM
        2: Wang et al. (2012) values from PREM
    -r X, --reference X: Reference frame for load love numbers
        CF: Center of Surface Figure (default)
        CM: Center of Mass of Earth System
        CE: Center of Mass of Solid Earth
    -l, --log: Output log of files created for each job
    -M X, --mode X: Permissions mode of the files created

PYTHON DEPENDENCIES:
    numpy: Scientific Computing Tools For Python
        https://numpy.org
        https://numpy.org/doc/stable/user/numpy-for-matlab-users.html
    netCDF4: Python interface to the netCDF C library
        https://unidata.github.io/netcdf4-python/netCDF4/index.html
    h5py: Pythonic interface to the HDF5 binary data format.
        https://www.h5py.org/
    future: Compatibility layer between Python 2 and Python 3
        https://python-future.org/

PROGRAM DEPENDENCIES:
    read_love_numbers.py: reads Load Love Numbers from Han and Wahr (1995)
    plm_holmes.py: Computes fully normalized associated Legendre polynomials
    gauss_weights.py: Computes the Gaussian weights as a function of degree
    ocean_stokes.py: reads a land-sea mask and converts to spherical harmonics
    gen_stokes.py: converts a spatial field into spherical harmonic coefficients
    harmonic_summation.py: calculates a spatial field from spherical harmonics
    harmonics.py: spherical harmonic data class for processing GRACE/GRACE-FO
        destripe_harmonics.py: calculates the decorrelation (destriping) filter
            and filters the GRACE/GRACE-FO coefficients for striping errors
        ncdf_read_stokes.py: reads spherical harmonic netcdf files
        ncdf_stokes.py: writes output spherical harmonic data to netcdf
        hdf5_read_stokes.py: reads spherical harmonic HDF5 files
        hdf5_stokes.py: writes output spherical harmonic data to HDF5
    spatial.py: spatial data class for reading, writing and processing data
        ncdf_read.py: reads input spatial data from netCDF4 files
        hdf5_read.py: reads input spatial data from HDF5 files
        ncdf_write.py: writes output spatial data to netCDF4
        hdf5_write.py: writes output spatial data to HDF5
    units.py: class for converting GRACE/GRACE-FO Level-2 data to specific units
    utilities.py: download and management utilities for files

REFERENCES:
    I Velicogna, T C Sutterley and M R van den Broeke. "Regional acceleration
        in ice mass loss from Greenland and Antarctica using GRACE
        time-variable gravity data". Geophysical Research Letters,
        41(22):8130-8137, 2014. https://doi.org/10.1002/2014GL061052

    T Jacob, J Wahr, W Pfeffer, and S C Swenson "Recent contributions of
        glaciers and ice caps to sea level rise". Nature, 482, 514-518 (2012).
        https://doi.org/10.1038/nature10847

    V M Tiwari, J Wahr, S and Swenson, "Dwindling groundwater resources in
        northern India, from satellite gravity observations",
        Geophysical Research Letters, 36(18), L18401, (2009).
        https://doi.org/10.1029/2009GL039401

UPDATE HISTORY:
    Updated 01/2021: harmonics object output from gen_stokes.py/ocean_stokes.py
    Updated 12/2020: added more love number options
    Updated 10/2020: use argparse to set command line parameters
    Updated 08/2020: use utilities to define path to load love numbers file
    Updated 04/2020: using the harmonics class for spherical harmonic operations
        updated load love numbers read function
    Updated 10/2019: changing Y/N flags to True/False
    Updated 10/2018: verify integers for python3 compatibility
    Updated 06/2018: using python3 compatible octal and input
    Updated 03/2018: added extrapolation of load love numbers if LMAX > 696
    Updated 09/2017: use a different land-sea mask for calculating ocean_Ylms
        use rcond=-1 in numpy least-squares algorithm
    Updated 05/2016: using __future__ print function
    Updated 02/2016: direct calculation of number of harmonics n_harm
        use getopt parameters to set number of PROCESSES to run in parallel,
            whether or not to output a log file, added new help module
    Updated 11/2015: create unique log filenames
    Updated 07/2015: added output of the sensitivity kernel Ylms in addition
        to the spatial fields (rather than just the spatial fields)
        will output logs with parameters and output_files
        added multiprocessing error handling with traceback
    Updated 05/2015: added parameter MMAX for LMAX != MMAX
        added portion to redistribute mascon mass uniformly over the ocean
    Updated 10/2014: distributed computing with the multiprocessing module
        added INTERVAL parameter for (degree spacing)/2
        input/output file type (ascii, netCDF4, HDF5)
    Updated 05/2014: added import functions
    Updated 02/2014: updated comments and added os.path.joins for connecting
        directories and files (generalizing code)
        some general updates to the program code
    Updated 08/2013: general updates to inputting data
        wrote grace_find_months, grace_input_months, gia_input
        to input spherical harmonics similar to python programs
    Updated 03/2012: edited to use new gen_stokes time-series option
    Written 02/2012
"""
from __future__ import print_function, division

import sys
import os
import time
import argparse
import numpy as np
import multiprocessing
import traceback

from gravity_toolkit.harmonics import harmonics
from gravity_toolkit.spatial import spatial
from gravity_toolkit.units import units
from gravity_toolkit.read_love_numbers import read_love_numbers
from gravity_toolkit.plm_holmes import plm_holmes
from gravity_toolkit.gauss_weights import gauss_weights
from gravity_toolkit.ocean_stokes import ocean_stokes
from gravity_toolkit.harmonic_summation import harmonic_summation
from gravity_toolkit.utilities import get_data_path

#-- PURPOSE: keep track of multiprocessing threads
def info(title):
    print(os.path.basename(sys.argv[0]))
    print(title)
    print('module name: {0}'.format(__name__))
    if hasattr(os, 'getppid'):
        print('parent process: {0:d}'.format(os.getppid()))
    print('process id: {0:d}'.format(os.getpid()))

#-- PURPOSE: read load love numbers for the range of spherical harmonic degrees
def load_love_numbers(LMAX, LOVE_NUMBERS=0, REFERENCE='CF'):
    """
    Reads PREM load Love numbers for the range of spherical harmonic degrees
    and applies isomorphic parameters

    Arguments
    ---------
    LMAX: maximum spherical harmonic degree

    Keyword arguments
    -----------------
    LOVE_NUMBERS: Load Love numbers dataset
        0: Han and Wahr (1995) values from PREM
        1: Gegout (2005) values from PREM
        2: Wang et al. (2012) values from PREM
    REFERENCE: Reference frame for calculating degree 1 love numbers
        CF: Center of Surface Figure (default)
        CM: Center of Mass of Earth System
        CE: Center of Mass of Solid Earth

    Returns
    -------
    kl: Love number of Gravitational Potential
    hl: Love number of Vertical Displacement
    ll: Love number of Horizontal Displacement
    """
    #-- load love numbers file
    if (LOVE_NUMBERS == 0):
        #-- PREM outputs from Han and Wahr (1995)
        #-- https://doi.org/10.1111/j.1365-246X.1995.tb01819.x
        love_numbers_file = get_data_path(['data','love_numbers'])
        header = 2
        columns = ['l','hl','kl','ll']
    elif (LOVE_NUMBERS == 1):
        #-- PREM outputs from Gegout (2005)
        #-- http://gemini.gsfc.nasa.gov/aplo/
        love_numbers_file = get_data_path(['data','Load_Love2_CE.dat'])
        header = 3
        columns = ['l','hl','ll','kl']
    elif (LOVE_NUMBERS == 2):
        #-- PREM outputs from Wang et al. (2012)
        #-- https://doi.org/10.1016/j.cageo.2012.06.022
        love_numbers_file = get_data_path(['data','PREM-LLNs-truncated.dat'])
        header = 1
        columns = ['l','hl','ll','kl','nl','nk']
    #-- LMAX of load love numbers from Han and Wahr (1995) is 696.
    #-- from Wahr (2007) linearly interpolating kl works
    #-- however, as we are linearly extrapolating out, do not make
    #-- LMAX too much larger than 696
    #-- read arrays of kl, hl, and ll Love Numbers
    hl,kl,ll = read_love_numbers(love_numbers_file, LMAX=LMAX, HEADER=header,
        COLUMNS=columns, REFERENCE=REFERENCE, FORMAT='tuple')
    #-- return a tuple of load love numbers
    return (hl,kl,ll)

#-- PURPOSE: calculate a regional time-series through a least
#-- squares mascon process
def calc_sensitivity_kernel(parameters, LOVE_NUMBERS=0, REFERENCE=None,
    MODE=0o775):
    #-- convert parameters to variables
    #-- spherical harmonic degree range
    LMIN = np.int(parameters['LMIN'])
    LMAX = np.int(parameters['LMAX'])
    #-- maximum spherical harmonic order
    if (parameters['MMAX'].title() == 'None'):
        MMAX = np.copy(LMAX)
    else:
        MMAX = np.int(parameters['MMAX'])
    #-- gaussian smoothing radius
    RAD = np.float(parameters['RAD'])
    #-- input/output data format (ascii, netCDF4, HDF5)
    DATAFORM = parameters['DATAFORM']
    #-- index of mascons spherical harmonics
    #-- path.expanduser = tilde expansion of path
    MASCON_INDEX = os.path.expanduser(parameters['MASCON_INDEX'])
    #-- output directory
    DIRECTORY = os.path.expanduser(parameters['DIRECTORY'])
    #-- 1: fit mass, 2: fit geoid
    FIT_METHOD = np.int(parameters['FIT_METHOD'])
    #-- mascon distribution
    MASCON_OCEAN = parameters['MASCON_OCEAN'] in ('Y','y')
    #-- spatial output parameters
    DDEG = np.array(parameters['DDEG'].split(','),dtype=np.float)
    DDEG = np.squeeze(DDEG)
    INTERVAL = np.int(parameters['INTERVAL'])

    #-- file information
    suffix = dict(ascii='txt', netCDF4='nc', HDF5='H5')

    #-- Create output Directory if not currently existing
    if (not os.access(DIRECTORY,os.F_OK)):
        os.mkdir(DIRECTORY)

    #-- list object of output files for file logs (full path)
    output_files = []

    #-- read arrays of kl, hl, and ll Love Numbers
    hl,kl,ll = load_love_numbers(LMAX, LOVE_NUMBERS=LOVE_NUMBERS,
        REFERENCE=REFERENCE)

    #-- Earth Parameters
    factors = units(lmax=LMAX).harmonic(hl,kl,ll)
    #-- Average Density of the Earth [g/cm^3]
    rho_e = factors.rho_e
    #-- Average Radius of the Earth [cm]
    rad_e = factors.rad_e

    #-- input/output string for both LMAX==MMAX and LMAX != MMAX cases
    order_str = 'M{0:d}'.format(MMAX) if (MMAX != LMAX) else ''

    #-- Calculating the Gaussian smoothing for radius RAD
    if (RAD != 0):
        wt = 2.0*np.pi*gauss_weights(RAD,LMAX)
        gw_str = '_r{0:0.0f}km'.format(RAD)
    else:
        #-- else = 1
        wt = np.ones((LMAX+1))
        gw_str = ''

    #-- Read Ocean function and convert to Ylms for redistribution
    if MASCON_OCEAN:
        #-- read Land-Sea Mask and convert to spherical harmonics
        LSMASK = os.path.expanduser(parameters['LANDMASK'])
        ocean_Ylms = ocean_stokes(LSMASK, LMAX, MMAX=MMAX, LOVE=(hl,kl,ll))
        ocean_str = '_OCN'
    else:
        #-- not distributing uniformly over ocean
        ocean_str = ''

    #-- input mascon spherical harmonic datafiles
    with open(MASCON_INDEX,'r') as f:
        mascon_files = f.read().splitlines()
    #-- number of mascons
    n_mas = len(mascon_files)
    #-- spatial area of the mascon
    total_area = np.zeros((n_mas))
    #-- name of each mascon
    mascon_name = []
    #-- for each valid file in the index (iterate over mascons)
    mascon_list = []
    for k,fi in enumerate(mascon_files):
        #-- read mascon spherical harmonics
        if (DATAFORM == 'ascii'):
            #-- ascii (.txt)
            Ylms = harmonics().from_ascii(os.path.expanduser(fi),date=False)
        elif (DATAFORM == 'netCDF4'):
            #-- netcdf (.nc)
            Ylms = harmonics().from_netCDF4(os.path.expanduser(fi),date=False)
        elif (DATAFORM == 'HDF5'):
            #-- HDF5 (.H5)
            Ylms = harmonics().from_HDF5(os.path.expanduser(fi),date=False)
        #-- Calculating the total mass of each mascon (1 cmwe uniform)
        total_area[k] = 4.0*np.pi*(rad_e**3)*rho_e*Ylms.clm[0,0]/3.0
        #-- distribute MASCON mass uniformly over the ocean
        if MASCON_OCEAN:
            #-- calculate ratio between total mascon mass and
            #-- a uniformly distributed cm of water over the ocean
            ratio = Ylms.clm[0,0]/ocean_Ylms.clm[0,0]
            #-- for each spherical harmonic
            for m in range(0,MMAX+1):#-- MMAX+1 to include MMAX
                for l in range(m,LMAX+1):#-- LMAX+1 to include LMAX
                    #-- remove ratio*ocean Ylms from mascon Ylms
                    #-- note: x -= y is equivalent to x = x - y
                    Ylms.clm[l,m] -= ratio*ocean_Ylms.clm[l,m]
                    Ylms.slm[l,m] -= ratio*ocean_Ylms.slm[l,m]
        #-- truncate mascon spherical harmonics to d/o LMAX/MMAX and add to list
        mascon_list.append(Ylms.truncate(lmax=LMAX, mmax=MMAX))
        #-- mascon base is the file without directory or suffix
        mascon_base = os.path.basename(mascon_files[k])
        mascon_base = os.path.splitext(mascon_base)[0]
        #-- if lower case, will capitalize
        mascon_base = mascon_base.upper()
        #-- if mascon name contains degree and order info, remove
        mascon_name.append(mascon_base.replace('_L{0:d}'.format(LMAX),''))
    #-- create single harmonics object from list
    mascon_Ylms = harmonics().from_list(mascon_list, date=False)

    #-- Output spatial data object
    grid = spatial()
    #-- Output Degree Spacing
    dlon,dlat = (DDEG,DDEG) if (np.ndim(DDEG) == 0) else (DDEG[0],DDEG[1])
    #-- Output Degree Interval
    if (INTERVAL == 1):
        #-- (-180:180,90:-90)
        n_lon = np.int((360.0/dlon)+1.0)
        n_lat = np.int((180.0/dlat)+1.0)
        grid.lon = -180 + dlon*np.arange(0,n_lon)
        grid.lat = 90.0 - dlat*np.arange(0,n_lat)
    elif (INTERVAL == 2):
        #-- (Degree spacing)/2
        grid.lon = np.arange(-180+dlon/2.0,180+dlon/2.0,dlon)
        grid.lat = np.arange(90.0-dlat/2.0,-90.0-dlat/2.0,-dlat)
        n_lon = len(grid.lon)
        n_lat = len(grid.lat)

    #-- Computing plms for converting to spatial domain
    theta = (90.0-grid.lat)*np.pi/180.0
    PLM,dPLM = plm_holmes(LMAX,np.cos(theta))

    #-- Calculating the number of cos and sin harmonics between LMIN and LMAX
    #-- taking into account MMAX (if MMAX == LMAX then LMAX-MMAX=0)
    n_harm=np.int(LMAX**2 - LMIN**2 + 2*LMAX + 1 - (LMAX-MMAX)**2 - (LMAX-MMAX))

    #-- Initialing harmonics for least squares fitting
    #-- mascon kernel
    M_lm = np.zeros((n_harm,n_mas))
    #-- mascon kernel converted to output unit
    MA_lm = np.zeros((n_harm,n_mas))
    #-- sensitivity kernel
    A_lm = np.zeros((n_harm,n_mas))
    #-- Initializing conversion factors
    #-- factor for converting to smoothed coefficients of mass
    fact = np.zeros((n_harm))
    #-- factor for converting back into geoid coefficients
    fact_inv = np.zeros((n_harm))
    #-- smoothing factor
    wt_lm = np.zeros((n_harm))

    #-- ii is a counter variable for building the mascon column array
    ii = 0
    #-- Creating column array of clm/slm coefficients
    #-- Order is [C00...C6060,S11...S6060]
    #-- Calculating factor to convert geoid spherical harmonic coefficients
    #-- to coefficients of mass (Wahr, 1998)
    coeff = rho_e*rad_e/3.0
    coeff_inv = 0.75/(np.pi*rho_e*rad_e**3)
    #-- Switching between Cosine and Sine Stokes
    for cs,csharm in enumerate(['clm','slm']):
        #-- copy cosine and sin harmonics
        mascon_harm = getattr(mascon_Ylms, csharm)
        #-- for each spherical harmonic degree
        #-- +1 to include LMAX
        for l in range(LMIN,LMAX+1):
            #-- for each spherical harmonic order
            #-- Sine Stokes for (m=0) = 0
            mm = np.min([MMAX,l])
            #-- +1 to include l or MMAX (whichever is smaller)
            for m in range(cs,mm+1):
                #-- Mascon Spherical Harmonics
                M_lm[ii,:] = np.copy(mascon_harm[l,m,:])
                #-- degree dependent factor to convert to mass
                fact[ii] = (2.0*l + 1.0)/(1.0 + kl[l])
                #-- degree dependent factor to convert from mass
                fact_inv[ii] = coeff_inv*(1.0 + kl[l])/(2.0*l+1.0)
                #-- degree dependent smoothing
                wt_lm[ii] = np.copy(wt[l])
                #-- add 1 to counter
                ii += 1

    #-- Converting mascon coefficients to fit method
    if (FIT_METHOD == 1):
        #-- Fitting Sensitivity Kernel as mass coefficients
        #-- converting M_lm to mass coefficients of the kernel
        for i in range(n_harm):
            MA_lm[i,:] = M_lm[i,:]*wt_lm[i]*fact[i]
        fit_factor = wt_lm*fact
        inv_fit_factor = np.copy(fact_inv)
    else:
        #-- Fitting Sensitivity Kernel as geoid coefficients
        for i in range(n_harm):
            MA_lm[:,:] = M_lm[i,:]*wt_lm[i]
        fit_factor = wt_lm*np.ones((n_harm))
        inv_fit_factor = np.ones((n_harm))

    #-- Fitting the sensitivity kernel from the input kernel
    for i in range(n_harm):
        #-- setting kern_i equal to 1 for d/o
        kern_i = np.zeros((n_harm))
        #-- converting to mass coefficients if specified
        kern_i[i] = 1.0*fit_factor[i]
        #-- spherical harmonics solution for the
        #-- mascon sensitivity kernels
        #-- Least Squares Solutions: Inv(X'.X).(X'.Y)
        kern_lm = np.linalg.lstsq(MA_lm,kern_i,rcond=-1)[0]
        for k in range(n_mas):
            A_lm[i,k] = kern_lm[k]*total_area[k]

    #-- for each mascon
    for k in range(n_mas):
        #-- reshaping harmonics of sensitivity kernel to LMAX+1,MMAX+1
        #-- calculating the spatial sensitivity kernel of each mascon
        #-- kernel calculated as outlined in Tiwari (2009) and Jacobs (2012)
        #-- Initializing output sensitivity kernel (both spatial and Ylms)
        kern_Ylms = harmonics(lmax=LMAX, mmax=MMAX)
        kern_Ylms.clm = np.zeros((LMAX+1,MMAX+1))
        kern_Ylms.slm = np.zeros((LMAX+1,MMAX+1))
        kern_Ylms.time = total_area[k]
        #-- counter variable for deconstructing the mascon column arrays
        ii = 0
        #-- Switching between Cosine and Sine Stokes
        for cs,csharm in enumerate(['clm','slm']):
            #-- for each spherical harmonic degree
            #-- +1 to include LMAX
            for l in range(LMIN,LMAX+1):
                #-- for each spherical harmonic order
                #-- Sine Stokes for (m=0) = 0
                mm = np.min([MMAX,l])
                #-- +1 to include l or MMAX (whichever is smaller)
                for m in range(cs,mm+1):
                    #-- inv_fit_factor: normalize from mass harmonics
                    temp = getattr(kern_Ylms, csharm)
                    temp[l,m] = inv_fit_factor[ii]*A_lm[ii,k]
                    #-- add 1 to counter
                    ii += 1

        #-- convert spherical harmonics to output spatial grid
        grid.data = harmonic_summation(kern_Ylms.clm, kern_Ylms.slm,
            grid.lon, grid.lat, LMAX=LMAX, MMAX=MMAX, PLM=PLM).T
        grid.time = total_area[k]

        #-- output names for sensitivity kernel Ylm and spatial files
        #-- for both LMAX==MMAX and LMAX != MMAX cases
        args = (mascon_name[k],ocean_str,LMAX,order_str,gw_str,suffix[DATAFORM])
        FILE1 = '{0}_SKERNEL_CLM{1}_L{2:d}{3}{4}.{5}'.format(*args)
        FILE2 = '{0}_SKERNEL{1}_L{2:d}{3}{4}.{5}'.format(*args)
        #-- output sensitivity kernel to file
        if (DATAFORM == 'ascii'):
            #-- ascii (.txt)
            kern_Ylms.to_ascii(os.path.join(DIRECTORY,FILE1),date=False)
            grid.to_ascii(os.path.join(DIRECTORY,FILE2),date=False,
                units='unitless',longname='Sensitivity_Kernel')
        elif (DATAFORM == 'netCDF4'):
            #-- netCDF4 (.nc)
            kern_Ylms.to_netCDF4(os.path.join(DIRECTORY,FILE1),date=False)
            grid.to_netCDF4(os.path.join(DIRECTORY,FILE2),date=False,
                units='unitless',longname='Sensitivity_Kernel')
        elif (DATAFORM == 'HDF5'):
            #-- netcdf (.H5)
            kern_Ylms.to_HDF5(os.path.join(DIRECTORY,FILE1),date=False)
            grid.to_HDF5(os.path.join(DIRECTORY,FILE2),date=False,
                units='unitless',longname='Sensitivity_Kernel')
        #-- change the permissions mode
        os.chmod(os.path.join(DIRECTORY,FILE1),MODE)
        os.chmod(os.path.join(DIRECTORY,FILE2),MODE)
        #-- add output files to list object
        output_files.append(os.path.join(DIRECTORY,FILE1))
        output_files.append(os.path.join(DIRECTORY,FILE2))

    #-- return the list of output files
    return output_files

#-- PURPOSE: print a file log for the mascon sensitivity kernel analysis
#-- lists: the parameter file, the parameters and the output files
def output_log_file(parameters,output_files):
    #-- format: calc_skernel_run_2002-04-01_PID-70335.log
    args = (time.strftime('%Y-%m-%d',time.localtime()), os.getpid())
    LOGFILE = 'calc_skernel_run_{0}_PID-{1:d}.log'.format(*args)
    DIRECTORY = os.path.expanduser(parameters['DIRECTORY'])
    #-- create a unique log and open the log file
    fid = create_unique_logfile(os.path.join(DIRECTORY,LOGFILE))
    #-- check if run from entering parameters or from parameter files
    if parameters['PARAMETER_FILE'] is not None:
        #-- print parameter file on top
        print('PARAMETER FILE:\n{0}\n\nPARAMETERS:'.format(
            os.path.abspath(parameters['PARAMETER_FILE'])), file=fid)
    else:
        print('PARAMETERS:', file=fid)
    #-- print parameter values sorted alphabetically
    for p in sorted(list(set(parameters.keys())-set(['PARAMETER_FILE']))):
        print('{0}: {1}'.format(p, parameters[p]), file=fid)
    #-- print output files
    print('\n\nOUTPUT FILES:', file=fid)
    for f in output_files:
        print('{0}'.format(f), file=fid)
    #-- close the log file
    fid.close()

#-- PURPOSE: print a error file log for the mascon sensitivity kernel analysis
#-- lists: the parameter file, the parameters and the error
def output_error_log_file(parameters):
    #-- format: calc_skernel_failed_run_2002-04-01_PID-70335.log
    args = (time.strftime('%Y-%m-%d',time.localtime()), os.getpid())
    LOGFILE = 'calc_skernel_failed_run_{0}_PID-{1:d}.log'.format(*args)
    DIRECTORY = os.path.expanduser(parameters['DIRECTORY'])
    #-- create a unique log and open the log file
    fid = create_unique_logfile(os.path.join(DIRECTORY,LOGFILE))
    #-- check if run from entering parameters or from parameter files
    if parameters['PARAMETER_FILE'] is not None:
        #-- print parameter file on top
        print('PARAMETER FILE:\n{0}\n\nPARAMETERS:'.format(
            os.path.abspath(parameters['PARAMETER_FILE'])), file=fid)
    else:
        print('PARAMETERS:', file=fid)
    #-- print parameter values sorted alphabetically
    for p in sorted(list(set(parameters.keys())-set(['PARAMETER_FILE']))):
        print('{0}: {1}'.format(p, parameters[p]), file=fid)
    #-- print traceback error
    print('\n\nTRACEBACK ERROR:', file=fid)
    traceback.print_exc(file=fid)
    #-- close the log file
    fid.close()

#-- PURPOSE: open a unique log file adding a numerical instance if existing
def create_unique_logfile(filename):
    #-- split filename into fileBasename and fileExtension
    fileBasename, fileExtension = os.path.splitext(filename)
    #-- create counter to add to the end of the filename if existing
    counter = 1
    while counter:
        try:
            #-- open file descriptor only if the file doesn't exist
            fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except OSError:
            pass
        else:
            return os.fdopen(fd, 'w+')
        #-- new filename adds counter the between fileBasename and fileExtension
        filename = '{0}_{1:d}{2}'.format(fileBasename, counter, fileExtension)
        counter += 1

#-- PURPOSE: define the analysis for multiprocessing
def define_analysis(f,LOVE_NUMBERS=0,REFERENCE=None,LOG=False,MODE=0o775):
    #-- keep track of multiprocessing threads
    info(os.path.basename(f))

    #-- variable with parameter definitions
    parameters = {}
    parameters['PARAMETER_FILE'] = f
    #-- Opening parameter file and assigning file ID number (fid)
    fid = open(os.path.expanduser(f), 'r')
    #-- for each line in the file will extract the parameter (name and value)
    for fileline in fid:
        #-- Splitting the input line between parameter name and value
        part = fileline.split()
        #-- filling the parameter definition variable
        parameters[part[0]] = part[1]
    #-- close the parameter file
    fid.close()

    #-- try to run the analysis with listed parameters
    try:
        #-- run calc sensitivity kernel algorithm with parameters
        output_files = calc_sensitivity_kernel(parameters,
            LOVE_NUMBERS=LOVE_NUMBERS, REFERENCE=REFERENCE, MODE=MODE)
    except:
        #-- if there has been an error exception
        #-- print the type, value, and stack trace of the
        #-- current exception being handled
        print('process id {0:d} failed'.format(os.getpid()))
        traceback.print_exc()
        if LOG:#-- write failed job completion log file
            output_error_log_file(parameters)
    else:
        if LOG:#-- write successful job completion log file
            output_log_file(parameters,output_files)

#-- This is the main part of the program that calls the individual modules
def main():
    #-- Read the system arguments listed after the program
    parser = argparse.ArgumentParser(
        description="""Calculates spatial sensitivity kernels through a
            least-squares mascon procedure
            """
    )
    #-- command line parameters
    parser.add_argument('parameters',
        type=lambda p: os.path.abspath(os.path.expanduser(p)), nargs='+',
        help='Parameter files containing specific variables for each analysis')
    #-- number of processes to run in parallel
    parser.add_argument('--np','-P',
        metavar='PROCESSES', type=int, default=0,
        help='Number of processes to run in parallel')
    #-- different treatments of the load Love numbers
    #-- 0: Han and Wahr (1995) values from PREM
    #-- 1: Gegout (2005) values from PREM
    #-- 2: Wang et al. (2012) values from PREM
    parser.add_argument('--love','-n',
        type=int, default=0, choices=[0,1,2],
        help='Treatment of the Load Love numbers')
    #-- option for setting reference frame for gravitational load love number
    #-- reference frame options (CF, CM, CE)
    parser.add_argument('--reference','-r',
        type=str.upper, default='CF', choices=['CF','CM','CE'],
        help='Reference frame for load Love numbers')
    #-- Output log file for each job in forms
    #-- calc_skernel_run_2002-04-01_PID-00000.log
    #-- calc_skernel_failed_run_2002-04-01_PID-00000.log
    parser.add_argument('--log','-l',
        default=False, action='store_true',
        help='Output log file for each job')
    #-- permissions mode of the local directories and files (number in octal)
    parser.add_argument('--mode','-M',
        type=lambda x: int(x,base=8), default=0o775,
        help='permissions mode of output files')
    args = parser.parse_args()

    #-- use parameter files from system arguments listed after the program.
    if (args.np == 0):
        #-- run directly as series if PROCESSES = 0
        #-- for each entered parameter file
        for f in args.parameters:
            define_analysis(f, LOVE_NUMBERS=args.love,
                REFERENCE=args.reference, LOG=args.log,
                MODE=args.mode)
    else:
        #-- run in parallel with multiprocessing Pool
        pool = multiprocessing.Pool(processes=args.np)
        #-- for each entered parameter file
        for f in args.parameters:
            kwds=dict(LOVE_NUMBERS=args.love, REFERENCE=args.reference,
                LOG=args.log, MODE=args.mode)
            pool.apply_async(define_analysis,args=(f,),kwds=kwds)
        #-- start multiprocessing jobs
        #-- close the pool
        #-- prevents more tasks from being submitted to the pool
        pool.close()
        #-- exit the completed processes
        pool.join()

#-- run main program
if __name__ == '__main__':
    main()
