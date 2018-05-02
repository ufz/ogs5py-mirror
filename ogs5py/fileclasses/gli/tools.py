#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
tools for the ogs5py-mesh package

@author: sebastian
"""
from __future__ import division, print_function, absolute_import
from copy import deepcopy as dcp
import numpy as np
from ogs5py.tools._types import (PLY_KEY_LIST, PLY_TYPES,
                                 SRF_KEY_LIST, SRF_TYPES,
                                 VOL_KEY_LIST, VOL_TYPES,
                                 GLI_KEY_LIST,
                                 EMPTY_GLI, EMPTY_PLY, EMPTY_SRF, EMPTY_VOL)


def load_ogs5gli(filepath, verbose=True):
    '''
    load a given OGS5 gli file

    Parameters
    ----------
    filepath : string
        path to the '*.msh' OGS5 mesh file to load
    verbose : bool, optional
        Print information of the reading process. Default: True

    Returns
    -------
    out : list of dictionaries
        each dictionary contains one '#FEM_MSH' block of the mesh file
        with the following information
            mesh_data : dictionary containing information about
                AXISYMMETRY (bool)
                CROSS_SECTION (bool)
                PCS_TYPE (str)
                GEO_TYPE (str)
                GEO_NAME (str)
                LAYER (int)
            nodes : ndarray
                Array with all node postions
            elements : dictionary
                contains nodelists for elements sorted by element types
            material_id : dictionary
                contains material ids for each element sorted by element types
            element_id : dictionary
                contains element ids for each element sorted by element types

    Notes
    -----
    The $AREA keyword within the Nodes definition is NOT supported
    and will violate the read data if present.
    '''

    out = dcp(EMPTY_GLI)

    with open(filepath, "r") as gli:
        # looping variable for reading
        reading = True
        # read the first line
        line = gli.readline().strip()
        while reading:
            # if end of file without '#STOP' keyword reached, raise Error
            filepos = gli.tell()
            if not gli.readline() and not line.startswith("#STOP"):
                raise EOFError("reached end of file... unexpected")
            gli.seek(filepos)

            # skip blank lines
            if not line:
                line = gli.readline().strip()
                continue

            # check for points
            elif line.startswith("#POINTS"):
                if verbose:
                    print("found 'POINTS'")
                pnts = np.empty((0, 3), dtype=float)
                names = []
                mds = []
                line = gli.readline().strip()
                while line and line[0].isdigit():
                    ln_splt = line.split()
                    # need a list around map in python3 (map gives iterator)
                    pnt = np.array(list(map(float, ln_splt[1:4])))
                    pnts = np.vstack((pnts, pnt))
                    if "$NAME" in ln_splt:
                        names.append(ln_splt[ln_splt.index("$NAME")+1])
                    else:
                        names.append("")
                    if "$MD" in ln_splt:
                        mds.append(float(ln_splt[ln_splt.index("$MD")+1]))
                    else:
                        # use -inf as standard md, if none is given
                        mds.append(-np.inf)
                    line = gli.readline().strip()
                out["points"] = pnts
                out["point_names"] = np.array(names, dtype=object)
                out["point_md"] = np.array(mds, dtype=float)
                continue

            # check for polyline
            elif line.startswith("#POLYLINE"):
                if verbose:
                    print("found 'POLYLINE'")
                ply = dcp(EMPTY_PLY)
                line = gli.readline().strip()
                # assure, that we are reading one polyline
                while not any([line.startswith(key) for key in GLI_KEY_LIST]):
                    need_new_line = True
                    key = line[1:]
                    if key in PLY_KEY_LIST:
                        if key == "POINTS":
                            ply["POINTS"] = []
                            line = gli.readline().strip()
                            while line and line.split()[0].isdigit():
                                ply["POINTS"].append(int(line.split()[0]))
                                line = gli.readline().strip()
                            if line in (GLI_KEY_LIST+["$"+k for
                                                      k in PLY_KEY_LIST]):
                                need_new_line = False
                            ply["POINTS"] = np.array(ply["POINTS"], dtype=int)
                        else:
                            ply_typ = PLY_TYPES[PLY_KEY_LIST.index(key)]
                            ply[key] = ply_typ(gli.readline().split()[0])
                    if need_new_line:
                        line = gli.readline().strip()
                out["polylines"].append(ply)
                continue

            # check for surface
            elif line.startswith("#SURFACE"):
                if verbose:
                    print("found 'SURFACE'")
                srf = dcp(EMPTY_SRF)
                line = gli.readline().strip()
                # assure, that we are reading one surface
                while not any([line.startswith(key) for key in GLI_KEY_LIST]):
                    need_new_line = True
                    key = line[1:]
                    if key in SRF_KEY_LIST:
                        if key == "POLYLINES":
                            srf["POLYLINES"] = []
                            line = gli.readline().strip()
                            while (line and line not in
                                   (GLI_KEY_LIST+["$"+k for
                                                  k in SRF_KEY_LIST])):
                                srf["POLYLINES"].append(str(line.split()[0]))
                                line = gli.readline().strip()
                            if line in (GLI_KEY_LIST+["$"+k for
                                                      k in SRF_KEY_LIST]):
                                need_new_line = False
                        else:
                            srf_typ = SRF_TYPES[SRF_KEY_LIST.index(key)]
                            srf[key] = srf_typ(gli.readline().split()[0])
                    if need_new_line:
                        line = gli.readline().strip()
                out["surfaces"].append(srf)
                continue

            # check for volume
            elif line.startswith("#VOLUME"):
                if verbose:
                    print("found 'VOLUME'")
                vol = dcp(EMPTY_VOL)
                line = gli.readline().strip()
                # assure, that we are reading one volume
                while not any([line.startswith(key) for key in GLI_KEY_LIST]):
                    need_new_line = True
                    key = line[1:]
                    if key in VOL_KEY_LIST:
                        if key == "SURFACES":
                            vol["SURFACES"] = []
                            line = gli.readline().strip()
                            while (line and line not in
                                   (GLI_KEY_LIST+["$"+k for
                                                  k in VOL_KEY_LIST])):
                                vol["SURFACES"].append(str(line.split()[0]))
                                line = gli.readline().strip()
                            if line in (GLI_KEY_LIST+["$"+k for
                                                      k in VOL_KEY_LIST]):
                                need_new_line = False
                        else:
                            vol_typ = VOL_TYPES[VOL_KEY_LIST.index(key)]
                            vol[key] = vol_typ(gli.readline().split()[0])
                    if need_new_line:
                        line = gli.readline().strip()
                out["volumes"].append(vol)
                continue

            # check for STOP
            elif line.startswith("#STOP"):
                if verbose:
                    print("found '#STOP'")
                # stop reading the file
                reading = False

            # handle unknown infos
            else:
                raise ValueError("file contains unknown infos: " +
                                 line.strip())

    return out


def save_ogs5gli(filepath, gli, top_com=None, verbose=True):
    '''
    save a given OGS5 mesh file

    Parameters
    ----------
    filepath : string
        path to the '*.msh' OGS5 mesh file to save
    gli : dict
        dictionary contains block from the gli file
        with the following information
            points : ndarray
                Array with all point postions
            point_names : ndarray (of strings)
                Array with all point names
            point_md : ndarray
                Array with all Material-densities at the points
                if point_md should be undefined it takes the value -np.inf
            polylines : list of dict, each containing information about
                "ID" (int or None)
                "NAME" (str)
                "POINTS" (ndarray)
                "EPSILON" (float or None)
                "TYPE" (int or None)
                "MAT_GROUP" (int or None)
                "POINT_VECTOR" (str or None)
            surfaces : list of dict, each containing information about
                "ID" (int or None)
                "NAME" (str)
                "POLYLINES" (list of str)
                "EPSILON" (float or None)
                "TYPE" (int or None)
                "MAT_GROUP" (int or None)
                "TIN" (str or None)
            volumes : list of dict, each containing information about
                "NAME" (str)
                "SURFACES" (list of str)
                "TYPE" (int or None)
                "MAT_GROUP" (int or None)
                "LAYER" (int or None)
    top_com : str, optional
        Comment to be added as header to the file, Default: None
    verbose : bool, optional
        Print information of the writing process. Default: True
    '''

    with open(filepath, "w") as gli_f:
        if top_com:
            if verbose:
                print("write top comment")
            print(str(top_com), file=gli_f)
        if verbose:
            print("write #POINTS")
        print("#POINTS", file=gli_f)
        # write all points
        for pnt_i, pnt in enumerate(gli["points"]):
            # generate NAME
            if gli["point_names"][pnt_i]:
                name = " $NAME "+str(gli["point_names"][pnt_i])
            else:
                name = ""
            # generate MD
            if gli["point_md"][pnt_i] == -np.inf:
                pnt_md = ""
            else:
                pnt_md = " $MD {}".format(gli["point_md"][pnt_i])
            # generate string for actual point
            tupl = (pnt_i,)+tuple(pnt)+(name, pnt_md)
            print("{} {} {} {}{}{}".format(*tupl), file=gli_f)

        if verbose:
            print("write #POLYLINES")
        # write all polylines
        for ply in gli["polylines"]:
            print("#POLYLINE", file=gli_f)
            # generate polyline
            for key in PLY_KEY_LIST:
                if key != "POINTS" and ply[key] is not None:
                    print(" $"+key, file=gli_f)
                    print("  {}".format(ply[key]), file=gli_f)
                elif ply[key] is not None:
                    print(" $POINTS", file=gli_f)
                    for pnt in ply["POINTS"]:
                        print("  {}".format(pnt), file=gli_f)

        if verbose:
            print("write #SURFACES")
        # write all surfaces
        for srf in gli["surfaces"]:
            print("#SURFACE", file=gli_f)
            # generate surface
            for key in SRF_KEY_LIST:
                if key != "POLYLINES" and srf[key] is not None:
                    print(" $"+key, file=gli_f)
                    print("  {}".format(srf[key]), file=gli_f)
                elif srf[key] is not None:
                    print(" $POLYLINES", file=gli_f)
                    for ply in srf["POLYLINES"]:
                        print("  {}".format(ply), file=gli_f)

        if verbose:
            print("write #VOLUMES")
        # write all volumes
        for vol in gli["volumes"]:
            print("#VOLUME", file=gli_f)
            # generate volume
            for key in VOL_KEY_LIST:
                if key != "SURFACES" and vol[key] is not None:
                    print(" $"+key, file=gli_f)
                    print("  {}".format(vol[key]), file=gli_f)
                elif vol[key] is not None:
                    print(" $SURFACES", file=gli_f)
                    for srf in vol["SURFACES"]:
                        print("  {}".format(srf), file=gli_f)

        if verbose:
            print("write #STOP")
        print("#STOP", end="", file=gli_f)


def load_media_prop_dist(filepath, verbose=True):
    '''
    load a given OGS5 '#MEDIUM_PROPERTIES_DISTRIBUTED' file

    Parameters
    ----------
    filepath : string
        path to the OGS5 '#MEDIUM_PROPERTIES_DISTRIBUTED' flie
    verbose : bool, optional
        Print information of the reading process. Default: True

    Returns
    -------
    out : dict
        dictionary contains the distributed properties stored in the given file
            key : string
                information of the key-value (string)
            DATA : float
                Array with all properties
    '''

    # initilize the output
    out = {}

    with open(filepath, "r") as mpd:
        # looping variable for reading
        reading = True
        found_start = False
        while reading:
            # read the next line
            line = mpd.readline()

            # if end of file without '$DATA' keyword reached, raise Error
            if not line:
                raise EOFError("reached end of file... unexpected")

            # skip blank lines
            elif not line.strip():
                continue

            # check for header
            elif line.split()[0] == "#MEDIUM_PROPERTIES_DISTRIBUTED":
                if found_start:
                    raise ValueError("corrupted file")
                else:
                    found_start = True
                    if verbose:
                        print("found '#MEDIUM_PROPERTIES_DISTRIBUTED'")

            # check for keywords
            elif line.split()[0][0] == "$":
                if not found_start:
                    raise ValueError("corrupted file")
                key = line.split()[0][1:]
                if verbose:
                    print("read '"+key+"'")
                # the important information is given by "DATA"
                if key == "DATA":
                    data = np.fromfile(mpd, sep=" ")
                    # get the IDs separatly
                    data_ids = data.reshape((-1, 2))[:, 0]
                    data_ids = data_ids.astype(int)
                    # reorder the values according to the IDs
                    # (if they are not sorted (possible?!))
                    data_val = data.reshape((-1, 2))[:, 1]
                    data_val = data_val[data_ids]
                    # store the data
                    out[key] = data_val
                    # stop reading
                    reading = False
                # return first line after keyword as value
                else:
                    out[key] = mpd.readline().split()

    return out