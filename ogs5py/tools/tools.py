#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
tools for the ogs5py-mesh package

@author: sebastian
"""
from __future__ import division, print_function, absolute_import
from copy import deepcopy as dcp
import numpy as np


def rotate_points(points, angle,
                  rotation_axis=(0., 0., 1.),
                  rotation_point=(0., 0., 0.)):
    '''
    Rotate points around a given rotation point and axis with a given angle.

    Parameters
    ----------
    points : ndarray
        Array with all points postions.
    angle : float
        rotation angle given in radial length
    rotation_axis : array_like, optional
        Array containing the vector for ratation axis. Default: (0,0,1)
    rotation_point : array_like, optional
        Array containing the vector for ratation base point. Default: (0,0,0)

    Returns
    -------
    new_array : ndarray
        rotated array
    '''
    rot = rotation_matrix(rotation_axis, angle)
    new_points = shift_points(points, -1.0*np.array(rotation_point))
    new_points = np.inner(rot, new_points).T
    new_points = shift_points(new_points, rotation_point)
    return new_points


def shift_points(points, vector):
    '''
    Shift points with a given vector.

    Parameters
    ----------
    points : ndarray
        Array with all points postions.
    vector : ndarray
        array containing the shifting vector

    Returns
    -------
    new_array : ndarray
        shifted array
    '''
    new_points = dcp(points)
    for i in range(3):
        new_points[:, i] += vector[i]
    return new_points


def transform_points(points, xyz_func, **kwargs):
    '''
    Transform points with a given function "xyz_func".
    kwargs will be forwarded to "xyz_func".

    Parameters
    ----------
    points : ndarray
        Array with all points postions.
    xyz_func : function
        the function transforming the points
        x_new, y_new, z_new = f(x_old, y_old, z_old, **kwargs)

    Returns
    -------
    new_array : ndarray
        transformed array
    '''
    trans = xyz_func(points[:, 0], points[:, 1], points[:, 2], **kwargs)
    return np.array(trans).T


def hull_deform(x_in, y_in, z_in,
                niv_top=10., niv_bot=0.,
                func_top=None, func_bot=None,
                direction="z"):
    '''
    Providing a transformation function to deform a given mesh in a given
    direction by self defined hull-functions ``z = func(x, y)``.
    Could be used with ``transform_mesh`` and ``transform_points``.

    Parameters
    ----------
    x_in : ndarray
        Array of the x-positions
    y_in : ndarray
        Array of the y-positions
    z_in : ndarray
        Array of the z-positions
    niv_top : float
        height of the top niveau to be deformed by func_top
    niv_bot : float
        height of the bottom niveau to be deformed by func_bot
    func_top : function or float
        function deforming the top niveau: ``z_top = func_top(x, y)``
    func_bot : function or float
        function deforming the bottom niveau: ``z_bot = func_bot(x, y)``
    direction : string, optional
        defining the direction of deforming. This direction will be used as
        z-value. Default: "z"

    Returns
    -------
    x_out, y_out, z_out : ndarray
        transformed arrays
    '''

    if direction == "x":
        x1_in = y_in
        x2_in = z_in
        x3_in = x_in
    elif direction == "y":
        x1_in = x_in
        x2_in = z_in
        x3_in = y_in
    else:
        x1_in = x_in
        x2_in = y_in
        x3_in = z_in

    if func_top is None:
        func_top = niv_top

    if func_bot is None:
        func_bot = niv_bot

    if isinstance(func_top, (float, int)):

        def func_top_redef(x_in, __):
            '''redefining func_top for constant value'''
            return float(func_top)*np.ones_like(x_in)

        func_t = func_top_redef
    else:
        func_t = func_top

    if isinstance(func_bot, (float, int)):

        def func_bot_redef(x_in, __):
            '''redefining func_bot for constant value'''
            return float(func_bot)*np.ones_like(x_in)

        func_b = func_bot_redef
    else:
        func_b = func_bot

    scale = (x3_in - niv_bot)/(niv_top - niv_bot)
    x3_out = scale*(func_t(x1_in, x2_in) -
                    func_b(x1_in, x2_in)) + func_b(x1_in, x2_in)

    if direction == "x":
        return x3_out, x1_in, x2_in
    elif direction == "y":
        return x1_in, x3_out, x2_in

    return x1_in, x2_in, x3_out


#####################
# helping functions #
#####################


def rotation_matrix(vector, angle):
    '''
    Create a rotation matrix for rotation around a given vector with a given
    angle.

    Parameters
    ----------
    vector : ndarray
        array containing the vector for ratation axis
    angle : float
        rotation angle given in radial length

    Returns
    -------
    result : ndarray
        matrix to be used for matrix multiplication with vectors to be
        rotated.
    '''
    # vector has to be normed
    vector = np.asfarray(vector)/np.linalg.norm(vector)
    mat = np.cross(np.eye(3), vector)
    cosa = np.cos(angle)
    sina = np.sin(angle)
    return cosa*np.eye(3) + sina*mat + (1-cosa)*np.outer(vector, vector)


def replace(arr, inval, outval):
    '''
    replace certain values of 'arr' defined in 'inval' with values defined
    in 'outval'

    Parameters
    ----------
    arr : ndarray
        array containing the input data
    inval : ndarray
        values appearing in 'arr' that should be replaced
    outval : ndarray
        values that should be written in 'arr' instead of values in 'inval'

    Returns
    -------
    result : ndarray
        array of the same shape as 'arr' containing the new data
    '''
    # convert input to numpy array
    inval = np.array(inval).reshape(-1)
    outval = np.array(outval).reshape(-1)
    arrtmp = np.copy(arr).reshape(-1)
    # sort inval and outval according to inval (needed for searchsorted)
    sort = np.argsort(inval)
    inval = inval[sort]
    outval = outval[sort]
    # replace values
    mask = np.in1d(arrtmp, inval)
    arrtmp[mask] = outval[np.searchsorted(inval, arrtmp[mask])]

    return arrtmp.reshape(arr.shape)


def unique_rows(data, decimals=4):
    '''
    returns unique made data with respect to given precision in "decimals"
    The output is sorted like the input data.
    data needs to be 2D

    Parameters
    ----------
    data : ndarray
        2D array containing the list of vectors that should be made unique
    decimals : int, optional
        Number of decimal places to round the 'data' to (default: 3).
        If decimals is negative, it specifies the number of positions
        to the left of the decimal point.
        This will not round the output, it is just for comparison of the
        vectors.

    Returns
    -------
    result : ndarray
        2D array of unique rows of data
    ix : ndarray
        index positions of output in input data (data[ix] = result)
        len(ix) = result.shape[0]
    ixr : ndarray
        reversed index positions of input in output data (result[ixr] = data)
        len(ixr) = data.shape[0]

    Notes
    -----
    This routine will preserve the order within the given array as effectively
    as possible. If you use it with a stack of 2 arrays and the first one is
    already unique, the resulting array will still have the first array at the
    beginning.
    '''
    if data.ndim != 2:
        raise ValueError("unique_rows: Wrong input shape. Only 2D allowed!")

    # round the input to the given precicion
    tmp = np.around(data, decimals=decimals)
    # using the 1D numpy 'unique' function by defining a special numpy dtype
    tmp = np.ascontiguousarray(tmp).view(np.dtype((np.void,
                                                   tmp.dtype.itemsize
                                                   * tmp.shape[1])))
    __, i_x, i_xr = np.unique(tmp, return_index=True, return_inverse=True)
    out = data[i_x]
    # sort the output according to the input
    sort = np.argsort(i_x)
    ixsort = i_x[sort]
    # this line is a pain in the ass/brain
    ixrsort = replace(i_xr, sort, np.arange(len(i_x)))

    return out[sort], ixsort, ixrsort