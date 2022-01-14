#################################################################
# TLSH is provided for use under two licenses: Apache OR BSD. Users
# may opt to use either license depending on the license
# restictions of the systems with which they plan to integrate the TLSH code.
#
# Apache License: # Copyright 2013 Trend Micro Incorporated
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may obtain a copy of the License at      http://www.apache.org/licenses/LICENSE-2.0
#
# BSD License: # Copyright (c) 2013, Trend Micro Incorporated. All rights reserved.
#
# see file "LICENSE
#################################################################

import csv
import sys
import tlsh
import numpy as np

from pylib.printCluster import *

##########################################
# creating tlsh pairwise distance for scipy and sklearn
##########################################

# https://stackabuse.com/hierarchical-clustering-with-python-and-scikit-learn/

from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import dendrogram, linkage
from matplotlib import pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.metrics import pairwise_distances
from sklearn.cluster import AgglomerativeClustering

verbose=0
tptr=[]

nDistCalc=0

def resetDistCalc():
    global nDistCalc
    nDistCalc=0

def lookupDistCalc():
    global nDistCalc
    return nDistCalc

def sim(idx1, idx2):
    global tptr
    global nDistCalc
    nDistCalc += 1

    # print("idx1=", idx1)
    # print("idx2=", idx2)
    h1 = tptr[int(idx1[0])]
    h2 = tptr[int(idx2[0])]
    dist=h1.diff(h2)
    return dist

def tlist2cdata(tlist):
    global tptr
    tptr=[]
    tidx = []
    idx=0
    for x in tlist:
        h1 = tlsh.Tlsh()
        h1.fromTlshStr(x)
        tptr.append(h1)
        elem=[ idx ]
        tidx.append(elem)
        idx += 1

    tdata = np.array(tidx)
    return tdata

##########################################
# tlsh_dendrogram
##########################################

def tlsh_dendrogram(tlist, labelList=None):
    if len(tlist) < 2:
        print("The list of tlsh is too short. len(tlist)=", len(tlist) )
        print("No dendrogram can be built.")
        return

    if len(tlist) >= 100:
        print("warning: The list of TLSH values is too long to show a sensible dendrogram.")
        print("It is recommended that you filter to a smaller list of TLSH values.")
        print()

    tdata = tlist2cdata(tlist)
    Y = pdist(tdata, sim)

    linked = linkage(Y, 'single')
    if labelList is None:
        labelList = range(1, len(tdata)+1)
    plt.figure(figsize=(15, 9))
    dendrogram(linked,
        orientation='left',
        labels=labelList,
        distance_sort='descending',
        show_leaf_counts=True)
    plt.show()

##########################################
# tlsh_csv files
##########################################

def tlsh_csvfile(fname, searchColName=None, searchValueList=None, simTlsh=None, simThreshold=150, sDate=None, eDate=None, searchNitems=None, verbose=0):
    # store the index for the different columns in the CSV file
    # instead of expecting a fixed order in the CSV files
    tlsh_column = -1
    hash_column = -1
    label_column = -1
    time_column = -1
    othCol = -1
    search_column = -1
    item_column = -1

    tlist = []
    labelList = []
    dateList = []
    hashList = []
    addSampleFlag = True

    if (simTlsh is not None) and (simThreshold == 150):
        if verbose > 0:
            print("using default simThreshold=150")

    # make all lower case so that we catch inconsistencies in the use of case
    if searchValueList is not None:
        searchValueList = [s.lower() for s in searchValueList]

    try:
        csv_file = open(fname)
    except:
        print("error: could not find file: " + fname, file=sys.stderr)
        return (None, None)

    # some counters for statistics
    line_count = 0
    valid_line_count = 0

    # read the CSV file. The first line should contain a valid
    # row header.
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        if line_count == 0:
            for x in range(len(row)):
                rval = row[x].lower()
                if (searchColName is not None) and (searchColName.lower() == rval):
                    search_column = x
                if rval == 'tlsh':
                    tlsh_column = x
                elif (rval == 'sha256') or (rval == 'sha1') or (rval == 'md5') or (rval == 'sha1_hash') or (rval == 'sha256_hash'):
                    hash_column = x
                elif (rval == 'signature') or (rval == 'label'):
                    # signature overrides other label candidates
                    if label_column != -1:
                        print("warning: found both 'signature' column and 'label' column")
                        print("using ", row[label_column] )
                    else:
                        label_column = x
                elif (rval == 'first_seen_utc') or (rval == 'firstseen'):
                    time_column = x
                elif rval == 'nitems':
                    item_column = x
                else:
                    if othCol == -1:
                        othCol = x
            if (label_column == -1) and (othCol != -1):
                if verbose > 0:
                    print("using " + row[othCol] + " as label")
                label_column = othCol

            if tlsh_column == -1:
                print("error: file " + fname + " has no tlsh column: " + str(row) )
                return (None, None)
            line_count += 1
        else:
            tlshVal = row[tlsh_column]

            # check if every line in the CSV is valid
            if tlshVal in ["TNULL", "", "n/a"]:
                line_count += 1
                continue

            if len(tlshVal) == 70 or ((len(tlshVal) == 72) and (tlshVal[:2] == "T1")):
                pass
            else:
                print("warning. Bad line line=", line_count, " tlshVal=", tlshVal )
                line_count += 1
                continue

            hashVal = row[hash_column] if (hash_column != -1) else ""
            lablVal = row[label_column] if (label_column != -1) else ""
            srchVal = row[search_column] if (search_column != -1) else ""
            itemVal = row[item_column] if (item_column != -1) else ""

            if time_column != -1:
                ts = row[time_column]
                # first_seen_utc (in malware bazaar) takes format "2021-09-17 06:39:44"
                # we want the first 10 characters
                dateVal = ts[:10]
            else:
                dateVal = ""

            if (label_column != -1) and (hash_column != -1):
                lab = lablVal + " " + hashVal
                lab = lablVal
            elif label_column != -1:
                lab = lablVal
            else:
                lab = hashVal

            # check search criteria
            includeLine = True
            if (srchVal != "") and (searchValueList is not None):
                if srchVal.lower() not in searchValueList:
                    includeLine = False

            if simTlsh is not None:
                h1 = tlsh.Tlsh()
                h1.fromTlshStr(simTlsh)
                h2 = tlsh.Tlsh()
                h2.fromTlshStr(tlshVal)
                dist=h1.diff(h2)
                if dist > simThreshold:
                    includeLine = False
                elif dist == 0:
                    # the search query is an item in our file
                    # so modify the label
                    # and do not add the Query
                    addSampleFlag = False
                    lab = "QUERY " + lab

            # check date range
            if (sDate is not None) and (dateVal != ""):
                if dateVal < sDate:
                    includeLine = False
            if (eDate is not None) and (dateVal != ""):
                # print("check dateVal=", dateVal, " eDate=", eDate)
                if dateVal > eDate:
                    includeLine = False

            # check item value
            if includeLine and (searchNitems is not None) and (itemVal != ""):
                if itemVal != str(searchNitems):
                    includeLine = False

            if includeLine:
                tlist.append(tlshVal)
                labelList.append(lab)
                dateList.append(dateVal)
                hashList.append(hashVal)

            valid_line_count += 1
            line_count += 1

    if verbose > 0:
        print(f'Read in {line_count} lines.')
        print(f'Read in {valid_line_count} valid lines.')

    if (simTlsh is not None) and (addSampleFlag):
        tlist.append(simTlsh)
        labelList.append("QUERY")
        dateList.append("")
        hashList.append("")
    return(tlist, [labelList, dateList, hashList])

##########################################
# assign clusters to points using sklearn
##########################################

def sim_affinity(tdata):
    return pairwise_distances(tdata, metric=sim)

def assignCluster(tlist, n_clusters):
    cluster = AgglomerativeClustering(n_clusters=n_clusters, affinity=sim_affinity, linkage='average')
    tdata = tlist2cdata(tlist)
    cluster_number = cluster.fit_predict(tdata)
    return cluster_number
# print(res)

def selectCluster(tlist, clusterNumber, clusterIdx, labelList=None):
    if clusterIdx not in clusterNumber:
        print("clusterIdx=" + str(clusterIdx) + " does not exist")
        return(None, None)
    cl_tlist = []
    cl_llist = []
    for xi in range(len(tlist)):
        if clusterNumber[xi] == clusterIdx:
            cl_tlist.append(tlist[xi])
            if labelList is None:
                cl_llist.append("cluster" + str(clusterIdx))
            else:
                cl_llist.append(labelList[xi])
    return(cl_tlist, cl_llist)

##########################################
# DBSCAN
##########################################

def runDBSCAN(tlist, eps, min_samples, algorithm='auto'):
    tdata = tlist2cdata(tlist)
    res = DBSCAN(eps=eps, min_samples=min_samples, metric=sim, algorithm=algorithm).fit(tdata)
    return res

def analyse_clusters(clusterNumber):
    nclusters = max(clusterNumber)
    members = []
    for x in range(nclusters+1):
        emptyList = []
        members.append(emptyList)
    print(members)
    print(len(members))
    noise = []
    for idx in range(len(clusterNumber)):
        cln = clusterNumber[idx]
        if cln != -1:
            members[cln].append(idx)
        else:
            noise.append(idx)
    for x in range(nclusters):
        print("cluster " + str(x) )
        print(members[x])
    print("noise: ")
    print(noise)

def outputClusters(outfname, tlist, clusterNumber, labelList, quiet=False):
    nclusters = max(clusterNumber)
    members = []
    for x in range(nclusters+1):
        emptyList = []
        members.append(emptyList)
    # print(members)
    # print(len(members))
    noise = []
    for idx in range(len(clusterNumber)):
        cln = clusterNumber[idx]
        if cln != -1:
            members[cln].append(idx)
        else:
            noise.append(idx)

    global tptr
    #
    # we call tlist2cdata to that we set tptr
    #
    tdata = tlist2cdata(tlist)

    # cluster is set to None since it is not used (by this program)
    cluster = None
    cenfname = ""
    verbose = 0
    if not quiet:
        verbose = 1
    printAllCluster(outfname, cenfname, cluster, members, tlist, tptr, labelList, verbose)
