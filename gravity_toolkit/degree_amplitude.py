#!/usr/bin/env python
u"""
degree_amplitude.py
Written Tyler Sutterley (07/2020)

Calculates the amplitude of each spherical harmonic degree

CALLING SEQUENCE:
    amp = degree_amplitude(clm,slm)

INPUTS:
    clm: cosine spherical harmonic coefficients
    slm: sine spherical harmonic coefficients

OPTIONS:
    LMAX: Upper bound of Spherical Harmonic Degrees
    MMAX: Upper bound of Spherical Harmonic Orders

PYTHON DEPENDENCIES:
    numpy: Scientific Computing Tools For Python (https://numpy.org)

UPDATE HISTORY:
    Updated 07/2020: added function docstrings
    Updated 05/2020: add singleton dimension to calculate time series amplitudes
    Updated 05/2015: added parameter MMAX for MMAX != LMAX
    Written 07/2013
"""
import numpy as np

def degree_amplitude(clm, slm, LMAX=None, MMAX=None):
    """
    Calculates the amplitude of each spherical harmonic degree

    Arguments
    ---------
    clm: cosine spherical harmonic coefficients
    slm: sine spherical harmonic coefficients

    Keyword arguments
    -----------------
    LMAX: Upper bound of Spherical Harmonic Degrees
    MMAX: Upper bound of Spherical Harmonic Orders

    Returns
    -------
    amp: degree amplitude
    """
    #-- add a singleton dimension to input harmonics
    if (np.ndim(clm) == 2):
        clm = np.copy(clm[:,:,None])
        slm = np.copy(slm[:,:,None])
    #-- check shape
    LMp1,MMp1,nt = np.shape(clm)

    #-- upper bound of spherical harmonic degrees
    if LMAX is None:
        LMAX = LMp1 - 1
    #-- upper bound of spherical harmonic orders
    if MMAX is None:
        MMAX = MMp1 - 1

    #-- allocating for output array
    amp = np.zeros((LMAX+1,nt))
    for l in range(LMAX+1):#-- m:LMAX
        m = np.arange(l,MMAX+1)
        #-- degree amplitude of spherical harmonic degree
        amp[l,:] = np.sqrt(np.sum(clm[l,m,:]**2 + slm[l,m,:]**2,axis=0))

    #-- return the degree amplitude with singleton dimensions removed
    return np.squeeze(amp)
