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

import sys
import datetime

import tlsh

from pylib.myheap import *
from pylib.printCluster import *
from pylib.tlsh_lib import *

###################################
# Global Vars
###################################

linearCheck = False
metricCheck = False
hac_allowStringyClusters = False
hac_verbose = 0

def median(currlist):
    newlist = sorted(currlist)
    listlen = len(currlist)
    mid = int((listlen-1)/2)
    return newlist[mid]


class Node:
    '''Vantage point tree'''
    def __init__(self, tobj, idx=-1, threshold=0):
        self._left_child = None
        self._right_child = None
        self.tobj = tobj
        self.idx = idx
        self.threshold = threshold

    @property
    def point(self):
        return self.tobj.hexdigest()

    @property
    def left_child(self):
        return self._left_child

    @left_child.setter
    def left_child(self, node):
        self._left_child = node

    @property
    def right_child(self):
        return self._right_child

    @right_child.setter
    def right_child(self, node):
        self._right_child = node

    # Print the tree
    def print_tree(self, maxdepth, depth):
        if depth > maxdepth:
            print("...")
            return

        if self.left_child is not None:
            self.left_child.print_tree(maxdepth, depth+1)
        print(depth * "\t", end="")
        if self.threshold == -1:
            print("LEAF:  idx=" + str(self.idx) + " " + self.point)
        else:
            print("SPLIT: idx=" + str(self.idx) + " " + self.point + " T=" + str(self.threshold))

        if self.right_child is not None:
            self.right_child.print_tree(maxdepth, depth+1)

def vpt_grow(tobjList, tidxList):
    lenList = len(tobjList)

    vpObj = tobjList[0]
    vpIdx = tidxList[0]

    if lenList == 1:
        thisNode = Node(vpObj, vpIdx, -1)
        return thisNode

    distList = [vpObj.diff(h1) for h1 in tobjList]

    # compute the median
    med = median(distList)

    # if med == 0:
    #     print("med = 0")
    #     print(distList)
    thisNode = Node(vpObj, vpIdx, med)

    # split data into two lists: left and right
    tobjLeft = []
    tidxLeft = []

    tobjRight = []
    tidxRight = []

    for li in range(1, lenList):
        if distList[li] < med:
            tobjLeft.append(tobjList[li])
            tidxLeft.append(tidxList[li])
        else:
            tobjRight.append(tobjList[li])
            tidxRight.append(tidxList[li])

    # recursively walk the data, unless there is no data
    if tobjLeft != []:
        thisNode.left_child = vpt_grow(tobjLeft,  tidxLeft)
    else:
        thisNode.left_child = None
    if tobjRight != []:
        thisNode.right_child = vpt_grow(tobjRight, tidxRight)
    else:
        thisNode.right_child = None
    return thisNode

def distMetric(tobj, searchItem):
    d = searchItem.diff(tobj)
    return d

extra_constant = 20

def VPTSearch(node, searchItem, searchIdx, cluster, notInC, best):
    if node is None:
        return

    d = distMetric(node.tobj, searchItem)
    if (cluster[node.idx] != notInC) and (d < best['dist']):
        best['dist'] = d
        best['point'] = node.point
        best['idx'] = node.idx

    if d <= node.threshold:
        VPTSearch(node.left_child, searchItem, searchIdx, cluster, notInC, best)
        if (d + best['dist'] + extra_constant) >= node.threshold:
            VPTSearch(node.right_child, searchItem, searchIdx, cluster, notInC, best)
        else:
            if metricCheck:
                rightbest = {"dist": best['dist'], "point": None, "idx": best['idx']}
                VPTSearch(node.right_child, searchItem, searchIdx, cluster, notInC, rightbest)
                if rightbest['idx'] != best['idx']:
                    print("found problem right", file=sys.stderr)
                    print("best:", best, file=sys.stderr)
                    print("d:", d, file=sys.stderr)
                    print("threshold:", node.threshold, file=sys.stderr)
                    print(rightbest, file=sys.stderr)
                    sys.exit(1)
    else:
        VPTSearch(node.right_child, searchItem, searchIdx, cluster, notInC, best)
        if (d - best['dist'] - extra_constant) <= node.threshold:
            VPTSearch(node.left_child, searchItem, searchIdx, cluster, notInC, best)
        else:
            if metricCheck:
                leftbest = {"dist": best['dist'], "point": None, "idx": best['idx']}
                VPTSearch(node.left_child, searchItem, searchIdx, cluster, notInC, leftbest)
                if leftbest['idx'] != best['idx']:
                    print("found problem left", file=sys.stderr)
                    print("best:", best, file=sys.stderr)
                    print("d:", d, file=sys.stderr)
                    print("threshold:", node.threshold, file=sys.stderr)
                    print(leftbest, file=sys.stderr)
                    sys.exit(1)

def Tentative_Merge(gA, gB, cluster, memberList, tobjList, rootVPT, CDist):
    global hac_verbose
    membersA = memberList[gA]
    for A in membersA:
        best = {"dist": 99999, "point": None, "idx": -1}
        searchItem = tobjList[A]
        VPTSearch(rootVPT, searchItem, A, cluster, gA, best)
        dist = best['dist']
        B = best['idx']
        if (dist <= CDist) and (cluster[A] != cluster[B]):
            ### print("success Tentative_Merge gA=", gA, " gB=", gB)
            ### print("A:", tlshList[A] )
            ### print("B:", tlshList[B] )
            ### print("dist:", dist )
            ### print("A=", A, best)

            ### print("before merge", gA, gB)
            ### printCluster(sys.stdout, gA, cluster, memberList, tlshList, tobjList, None)
            ### printCluster(sys.stdout, gB, cluster, memberList, tlshList, tobjList, None)

            if hac_verbose >= 1:
                print("Merge(2) A=", A, " B=", B, " dist=", dist)
            newCluster = Merge(cluster[A], cluster[B], cluster, memberList, tobjList, dist)
            if hac_verbose >= 2:
                print("success Tentative_Merge gA=", gA, " gB=", gB)
            return 1

    if hac_verbose >= 2:
        print("failed Tentative_Merge gA=", gA, " gB=", gB)
    return 0

def Merge(gA, gB, cluster, memberList, tobjList, dist):
    # radA = estimateRadius(memberList[gA], tobjList)
    # radB = estimateRadius(memberList[gB], tobjList)
    # print("before merge", gA, gB)
    # printCluster(gA, cluster, memberList)
    # printCluster(gB, cluster, memberList)
    if gA == gB:
        print("warning in Merge gA=", gA, " gB=", gB)
        return gA

    minA = min(memberList[gA])
    minB = min(memberList[gB])

    # the new cluster is the one with the smallest element
    if minA < minB:
        c1 = gA
        c2 = gB
    else:
        c1 = gB
        c2 = gA

    membersA = memberList[c1]
    for x in memberList[c2]:
        ### print("x=", x)
        membersA.append(x)
        cluster[x] = c1
    memberList[c2] = []

    # print("after merge", gA, gB)
    # printCluster(gA, cluster, memberList)
    # printCluster(gB, cluster, memberList)
    # radc1 = estimateRadius(memberList[c1], tobjList)
    # if radc1 > 30:
    #    print("ERROR before merge:    rad(A)=", radA, " rad(B)=", radB, " dist=", dist, "    after rad=", radc1)
    return c1

def linearSearch(searchItem, tobjList, ignoreList, linbest):
    bestScore = 9999999
    bestIdx = -1
    for ti in range(0, len(tobjList)):
        if ti not in ignoreList:
            h1 = tobjList[ti]
            d = searchItem.diff(h1)
            if d < bestScore:
                bestScore = d
                bestIdx = ti

    linbest['dist'] = bestScore
    linbest['idx'] = bestIdx

def VPTsearch_add_to_heap(A, cluster, tobjList, rootVPT, heap):
    best = {"dist": 99999, "point": None, "idx": -1}
    searchItem = tobjList[A]
    ignoreList = [A]
    VPTSearch(rootVPT, searchItem, A, cluster, cluster[A], best)
    dist = best['dist']
    if dist < 99999:
        B = best['idx']
        rec = {'pointA': A, 'pointB': B, 'dist': dist}
        heap.insert(rec, dist)
        ### :print("heap insert: ", rec)

        if linearCheck:
            linbest = {"dist": 99999, "point": None, "idx": -1}
            linearSearch(searchItem, tobjList, ignoreList, linbest)
            lindist = linbest['dist']
            linB = linbest['idx']
            if lindist < dist:
                print("error: dist=", dist, "B=", B, file=sys.stderr)
                print("error: lindist=", lindist, "linB=", linB, file=sys.stderr)
                sys.exit()

showTiming = 1
prev = None
startTime = None

showNumberClusters = 0

def setNoTiming():
    global showTiming
    showTiming = 0

def setShowNumberClusters():
    global showNumberClusters
    showNumberClusters = 1

def print_time(title, final=0):
    global showTiming
    global prev
    global startTime
    if showTiming == 0:
        return

    now = datetime.datetime.now()
    print(title + ":\t" + str(now))

    if prev is None:
        startTime = now
    else:
        tdelta = (now - prev)
        delta_micro = tdelta.microseconds + tdelta.seconds * 1000000
        delta_ms = delta_micro // 1000
        print(title + "-ms:\t" + str(delta_ms))

    if final == 1:
        tdelta = now - startTime
        delta_micro = tdelta.microseconds + tdelta.seconds * 1000000
        delta_ms = delta_micro // 1000
        print("time-ms:\t" + str(delta_ms))

    prev = now

def print_number_clusters(memberList, end=False):
    count = 0
    single = 0
    for ci in range(0, len(memberList)):
        ml = memberList[ci]
        if len(ml) == 1:
            single += 1
        elif len(ml) > 1:
            count += 1

    if end:
        print("ENDncl=", count, "\tnsingle=", single)
    else:
        print("ncl=", count, "\tnsingle=", single)

def HAC_T_step3(tobjList, CDist, rootVPT, memberList, cluster):
    global hac_verbose

    ITERATION = 1
    clusters_to_examine = []
    for ci in range(0, len(memberList)):
        ml = memberList[ci]
        if len(ml) > 1:
            clusters_to_examine.append(ci)

    while len(clusters_to_examine) > 0:
        global showNumberClusters
        if (hac_verbose >= 1) or (showNumberClusters >= 1):
            print("ITERATION ", ITERATION)
            print_number_clusters(memberList)

        lmodified = []
        for ci in clusters_to_examine:
            ml = memberList[ci]
            if hac_verbose >= 2:
                print("checking cluster: ci=", ci, " ", ml)
            for A in ml:
                best = {"dist": 99999, "point": None, "idx": -1}
                searchItem = tobjList[A]
                VPTSearch(rootVPT, searchItem, A, cluster, cluster[A], best)
                dist = best['dist']
                if dist <= CDist:
                    B = best['idx']

                    mergeOK = True
                    if not hac_allowStringyClusters:
                        newml = memberList[cluster[A]] + memberList[cluster[B]]
                        newrad = estimateRadius(newml, tobjList)
                        if newrad > CDist:
                            if hac_verbose >= 2:
                                radA = estimateRadius(memberList[cluster[A]], tobjList)
                                radB = estimateRadius(memberList[cluster[B]], tobjList)
                                print("failed merge:\tdist(A=", A, ",B=", B, ") =", dist, " rad(A)=", radA, " rad(B)=", radB, " newrad=", newrad)
                            mergeOK = False

                    if mergeOK:
                        if hac_verbose >= 2:
                            print("merging as dist(A=", A, ",B=", B, ") =", dist, " need to go again...")
                            printCluster(sys.stdout, cluster[A], cluster, memberList, tobjList, None)
                            printCluster(sys.stdout, cluster[B], cluster, memberList, tobjList, None)

                        if hac_verbose >= 1:
                            print("Merge(3) A=", A, " B=", B, " dist=", dist)
                        newCluster = Merge(cluster[A], cluster[B], cluster, memberList, tobjList, dist)
                        if newCluster not in lmodified:
                            lmodified.append(newCluster)
                        break

        clusters_to_examine = lmodified
        ITERATION += 1

    return ITERATION

def HAC_T_opt(fname, CDist, step3, outfname, cenfname, verbose=0):
    global hac_verbose
    hac_verbose = verbose
    global hac_allowStringyClusters
    hac_allowStringyClusters = True

    # Step 0: read in data
    (tobjList, labels) = read_data(fname)
    tidxList = range(0, len(tobjList))

    # Step 1: Preprocess data / Grow VPT
    ndata = len(tobjList)
    if ndata >= 1000:
        print_time("Start")

    rootVPT = vpt_grow(tobjList, tidxList)

    cluster = list(range(0, ndata))
    heap = MinHeap()
    for A in range(ndata):
        VPTsearch_add_to_heap(A, cluster, tobjList, rootVPT, heap)

    if ndata >= 1000:
        print_time("End-Step-1")

    # Step 2: Cluster data (HAC_T_opt)
    memberList = []
    for A in range(ndata):
        mlist = [A]
        memberList.append(mlist)

    global showNumberClusters
    if (hac_verbose >= 1) or (showNumberClusters >= 1):
        print_number_clusters(memberList)

    while heap.nelem() > 0:
        rec = heap.deleteTop()
        A = rec['pointA']
        B = rec['pointB']
        d = rec['dist']
        if (d <= CDist) and (cluster[A] != cluster[B]):
            newCluster = Merge(cluster[A], cluster[B], cluster, memberList, tobjList, d)

    if (hac_verbose >= 1) and (ndata >= 1000):
        print_time("End-Step-2")

    # Step 3: Find clusters which need to be merged
    if (hac_verbose >= 1) or (showNumberClusters >= 1):
        print_number_clusters(memberList)
    if step3 == 0:
        if hac_verbose >= 1:
            print_time("Not-doing-Step-3", 1)
    else:
        HAC_T_step3(tobjList, CDist, rootVPT, memberList, cluster)
        if (hac_verbose >= 1) and (ndata >= 1000):
            print_time("End-Step-3", 1)

    if (hac_verbose >= 1) or (showNumberClusters >= 1):
        print_number_clusters(memberList, True)
    printAllCluster(outfname, cenfname, cluster, memberList, tobjList, labels, hac_verbose)

def HAC_T(fname, CDist, step3, outfname, cenfname, allowStringy=0, verbose=0):
    global hac_verbose
    hac_verbose = 0
    global hac_allowStringyClusters
    hac_allowStringyClusters = allowStringy

    # Step 0: read data
    (tobjList, labels) = read_data(fname)
    tidxList = range(0, len(tobjList))

    # Step 1: Initialise / Grow VPT
    ndata = len(tobjList)
    if (hac_verbose >= 1) and (ndata >= 1000):
        print_time("Start")

    rootVPT = vpt_grow(tobjList, tidxList)

    # Step 2: Cluster data
    cluster = list(range(0, ndata))
    memberList = []
    for A in range(ndata):
        mlist = [A]
        memberList.append(mlist)

    if (hac_verbose >= 1) or (showNumberClusters >= 1):
        print_number_clusters(memberList)

    tent_heap = MinHeap()
    tent_dict = {}
    for A in range(ndata):
        best = {"dist": 99999, "point": None, "idx": -1}
        searchItem = tobjList[A]
        VPTSearch(rootVPT, searchItem, A, cluster, cluster[A], best)
        dist = best['dist']
        B = best['idx']
        if hac_verbose >= 2:
            print("VPT: A=", A, " B=", B, " dist=", dist)
        if (B != -1) and (cluster[A] == cluster[B]):
            print("error: A=", A, "B=", B, file=sys.stderr)
            sys.exit(1)

        if dist <= CDist:
            mergeOK = True
            if not hac_allowStringyClusters:
                newml = memberList[cluster[A]] + memberList[cluster[B]]
                newrad = estimateRadius(newml, tobjList)
                if newrad > CDist:
                    if hac_verbose >= 2:
                        radA = estimateRadius(memberList[cluster[A]], tobjList)
                        radB = estimateRadius(memberList[cluster[B]], tobjList)
                        print("failed merge: dist(A=", A, ",B=", B, ") =", dist, " rad(A)=", radA, " rad(B)=", radB, " newrad=", newrad)
                    mergeOK = False

            if mergeOK:
                if hac_verbose >= 1:
                    print("Merge(1) A=", A, " B=", B, " dist=", dist)
                newCluster = Merge(cluster[A], cluster[B], cluster, memberList, tobjList, dist)

        elif (dist <= 2 * CDist) and (hac_allowStringyClusters):
            if hac_verbose >= 2:
                print("Tentative_Merge A=", A, " B=", B, " dist=", dist)
            cluster1 = cluster[A]
            cluster2 = cluster[B]
            if cluster1 < cluster2:
                tent2 = str(cluster1) + ":" + str(cluster2)
            else:
                tent2 = str(cluster2) + ":" + str(cluster1)

            if tent2 not in tent_dict:
                tent_dict[tent2] = 1
                rec = {'pointA': A, 'pointB': B, 'dist': dist}
                tent_heap.insert(rec, dist)

    if (hac_verbose >= 1) or (showNumberClusters >= 1):
        print_number_clusters(memberList)
    count_tentative_success = 0
    count_tentative_fail = 0
    count_tentative_already_done = 0

    while tent_heap.nelem() > 0:
        rec = tent_heap.deleteTop()
        A = rec['pointA']
        B = rec['pointB']
        d = rec['dist']
        if cluster[A] != cluster[B]:
            res = Tentative_Merge(cluster[A], cluster[B], cluster, memberList, tobjList, rootVPT, CDist)
            if res > 0:
                count_tentative_success += 1
            else:
                count_tentative_fail += 1
        else:
            count_tentative_already_done += 1

    if hac_verbose >= 1:
        print("tentative_already_done\t=", count_tentative_already_done)
        print("tentative_success\t=", count_tentative_success)
        print("tentative_fail\t\t=", count_tentative_fail)

    if (hac_verbose >= 1) and (ndata >= 1000):
        print_time("End-Step-2", 1)

    # Step 3: Find Edge Cases
    if (hac_verbose >= 1) or (showNumberClusters >= 1):
        print_number_clusters(memberList)
    if step3 == 0:
        if (hac_verbose >= 1) and (ndata >= 1000):
            print_time("Not-doing-Step-3")
    else:
        ITERATION = HAC_T_step3(tobjList, CDist, rootVPT, memberList, cluster)
        if ITERATION != 2:
            print("INFO: NOT OPTIMAL CLUSTERING")
        if (hac_verbose >= 1) and (ndata >= 1000):
            print_time("End-Step-3")

    if (hac_verbose >= 1) or (showNumberClusters >= 1):
        print_number_clusters(memberList, True)
    printAllCluster(outfname, cenfname, cluster, memberList, tobjList, labels, hac_verbose)

    cln = 0
    dbscan_like_cluster = [-1] * len(cluster)
    for ci in range(0, len(memberList)):
        ml = memberList[ci]
        if len(ml) > 1:
            for x in ml:
                dbscan_like_cluster[x] = cln
            cln += 1

    return dbscan_like_cluster

def DBSCAN_procedure(fname, CDist, outfname, cenfname, verbose=0):
    (tlist, labels) = tlsh_csvfile(fname)
    res = runDBSCAN(tlist, eps=CDist, min_samples=2)
    outputClusters(outfname, tlist, res.labels_, labels)
    return res.labels_

def read_data(fname):
    (tlshList, labels) = tlsh_csvfile(fname)
    tobjList = []
    for tstr in tlshList:
        h1 = tlsh.Tlsh()
        h1.fromTlshStr(tstr)
        tobjList.append(h1)
    return (tobjList, labels)

def estimateRadius(ml, tobjList):
    nlist = len(ml)

    # sample max 100 points to determine the radius
    nsteps = 100
    jump = int(nlist / nsteps)
    maxni = jump * nsteps
    if jump == 0:
        jump = 1
        maxni = nlist

    rad_cluster = 99999
    rad_idx = -1

    for xi in range(0, maxni, jump):
        x = ml[xi]
        hx = tobjList[x]
        radx = 0
        for yi in range(0, maxni, jump):
            y = ml[yi]
            if x != y:
                hy = tobjList[y]
                d = hx.diff(hy)
                if d > radx:
                    radx = d

        if radx < rad_cluster:
            rad_cluster = radx
            rad_idx = x

    return rad_cluster
