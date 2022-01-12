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

from collections import Counter

def printAllCluster(outfname, cenfname, cluster, memberList, tlshList, tobjList, labels, verbose):
    '''Write cluster and centers output files'''

    # cluster output file
    f = open(outfname, "w")
    if f is None:
        print("error: cannot write  to ", outfname)
        return

    # centers output file (csv file of cluster centers)
    cenf = None
    if cenfname != "":
        cenf = open(cenfname, "w")
        if cenf is None:
            print("error: cannot write  to ", cenfname)
            return
        cenf.write("tlsh,family,firstSeen,label,radius,nitems\n")

    labelList = labels[0]
    dateList  = labels[1]

    for ci in range(0, len(memberList) ):
        ml = memberList[ci]
        if len(ml) > 1:
            printCluster(f, cenf, ci, cluster, memberList, tlshList, tobjList, labelList, dateList)

    f.close()
        print("written ", outfname)

    if cenfname != "":
        cenf.close()
        if verbose >= 1:
            print("written ", cenfname)

def printCluster(f, cenf, gA, cluster, memberList, tlshList, tobjList, labelList, dateList):
    outml = sorted(memberList[gA])
    rad_cluster = 99999
    rad_idx     = -1
    labelSet    = set()
    nitems = len(outml)
    for x in outml:
        hx = tobjList[x]
        radx=0
        for y in outml:
            if x != y:
                hy = tobjList[y]
                d = hx.diff(hy)
                if d > radx:
                    radx = d

        if radx < rad_cluster:
            rad_cluster = radx
            rad_idx = x

        if (labelList is not None) and (len(labelList) > 0):
            if labelList[x] != "NO_SIG":
                labelSet.add(labelList[x].lower())

    # identify the most common label
    nlabel=len(labelSet)
    labelMostCommon = "NULL"
    if nlabel == 0:
        labelStr = ""
    else:
        labelStr = str( sorted(list(labelSet)) )
        tmpList = [labelList[x] for x in outml if labelList[x] != "n/a"]
        if len(tmpList) > 0:
            c = Counter(tmpList)
            labelMostCommonTuple = c.most_common(1)[0]
            labelMostCommon = labelMostCommonTuple[0]

    # identify the first time value
    firstSeen = "NULL"
    if dateList is not None:
        clusterTimeList = [dateList[x] for x in outml]
        firstSeen = min( clusterTimeList )
        tmpList = [labelList[x] for x in outml if labelList[x] != "n/a"]

    f.write("members:\t" + str(outml) + "\n" )
    f.write("labels:\t" + labelStr + "\n" )
    f.write("nlabels:\t" + str(nlabel) + "\n" )
    f.write("nitems:\t" + str(nitems) + "\n" )
    f.write("center:\t" + tlshList[rad_idx] + "\n" )
    f.write("radius:\t" + str(rad_cluster) + "\n" )

    if len(labelList) > 0:
        for x in outml:
            f.write("\t" + tlshList[x] + "\t" + labelList[x] + "\n")

    else:
        for x in outml:
            f.write("\t" + tlshList[x] + "\n")

    if cenf is not None:
        if labelMostCommon == "NULL":
            labelMostCommon = "Cluster " + str(gA)
        label_date = labelMostCommon + " " + firstSeen + " (" + str(nitems) + ")"

        cenf.write(tlshList[rad_idx] + "," )
        cenf.write(labelMostCommon + "," )
        cenf.write(firstSeen + "," )
        cenf.write(label_date + "," )
        cenf.write(str(rad_cluster) + "," )
        cenf.write(str(nitems))
        cenf.write("\n" )
