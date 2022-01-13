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
import tlsh

from pylib.printCluster import *
from pylib.tlsh_lib import *

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

##########################################
# show a malware bazaar cluster
##########################################
def mb_show_sha1(family, thisDate=None, nitems=None, fname="malbaz/clust_389300.csv", showN=10, showC=1):
    (tlist, labels) = tlsh_csvfile(fname, searchColName="family", searchValueList=[family], sDate=thisDate, eDate=thisDate, searchNitems=nitems)
    if tlist is None:
        return
    if len(tlist) == 0:
        print("found no cluster")
    elif len(tlist) <= showC:
        for cenTlsh in tlist:
            print("cluster with cenTlsh=" + cenTlsh)
            fullmb = "malbaz/mb_full.csv"
            (tlist2, labels2) = tlsh_csvfile(fullmb, simTlsh=cenTlsh, simThreshold=30)
            if tlist2 is None:
                print("you need to run the script process_mb.sh in malbaz")
                return

            nfound = len(tlist2)
            if nfound > showN:
                print("showing first ", showN, " samples")
                print("increase the showN parameter to show more..." )
                nfound = showN

            labList  = labels2[0]
            dateList = labels2[1]
            hashList = labels2[2]
            for idx in range(nfound):
                # print(tlist2[idx] + "\t" + labList[idx] + "\t" + dateList[idx] + "\t" + hashList[idx] )
                print(hashList[idx] )
    else:
        print("found ", len(tlist), " clusters.")
        print("Use parameters 'thisDate' and 'nitems' to uniquely specify cluster")
        print("OR")
        print("set showC parameter to show more clusters")
