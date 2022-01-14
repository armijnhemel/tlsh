import argparse
import datetime
import pathlib
import sys

from pylib.hac_lib import *


##############################################
# simple_unittests()
##############################################

def simple_unittests(fname):
    (tobj_list, labels) = read_data(fname)

    tidx_list = range(0, len(tobj_list))
    root = vpt_grow(tobj_list, tidx_list)
    root.print_tree(3, 0)

    ### id = 9655
    identifier = 9

    best = {"dist": 99999, "point": None, "idx": -1}
    ignore_list = [identifier]
    search_item = tobj_list[identifier]

    tmpcluster = list(range(0, len(tobj_list)))

    print("before: ", best)
    VPTSearch(root, search_item, identifier, tmpcluster, identifier, best)
    print("after:  ", best)

    dist = best['dist']
    B = best['idx']
    linbest = {"dist": 99999, "point": None, "idx": -1}
    linearSearch(search_item, tobj_list, ignore_list, linbest)
    lindist = linbest['dist']
    linB = linbest['idx']
    if lindist < dist:
        print("error: dist=", dist, "B=", B, file=sys.stderr)
        print("error: lindist=", lindist, "linB=", linB, file=sys.stderr)
        sys.exit()

    ### heap_tester()

def main():
    parser = argparse.ArgumentParser(prog='hac')
    parser.add_argument('-v', help='verbose', type=int, default=0)
    parser.add_argument('-opt', help='opt', type=int, default=0)
    parser.add_argument('-dbscan', help='dbscan', type=int, default=0)
    parser.add_argument('-allow', help='allow stringy clusters', type=int, default=0)
    parser.add_argument('-cdist', help='cdist', type=int, default=30)
    parser.add_argument('-f', help='fname', type=str, default="")
    parser.add_argument('-o', help='outfname', type=str, default="")
    parser.add_argument('-oc', help='out centers fname', type=str, default="")
    parser.add_argument('-step3', help='step3', type=int, default=1)
    parser.add_argument('-showtime', help='showtime', type=int, default=0)
    parser.add_argument('-showcl', help='show number clusters', type=int, default=0)
    parser.add_argument('-utest', help='unittest', type=int, default=0)

    args = parser.parse_args()
    verbose = args.v
    opt = args.opt
    dbscan = args.dbscan
    allow = args.allow
    CDist = args.cdist
    fname = pathlib.Path(args.f)
    outfname = args.o
    cenfname = args.oc
    step3 = args.step3
    showtime = args.showtime
    showcl = args.showcl
    unittest = args.utest

    if opt == 0:
        linear_check = False

    if showtime <= 1:
        ###############
        # showtime == 0 no timing performed
        # showtime == 1 time the overall program
        # showtime == 2 time parts of the algorithm
        ###############
        setNoTiming()

    if showcl:
        setShowNumberClusters()

    if fname == "":
        print("need a -f fname", file=sys.stderr)
        sys.exit(1)

    if not fname.exists():
        print("File %s does not exist" % fname, file=sys.stderr)
        sys.exit(1)

    if outfname == "":
        print("need a -o outfname", file=sys.stderr)
        sys.exit(1)

    if unittest > 0:
        simple_unittests(fname)

    if showtime == 1:
        start_time = datetime.datetime.now()

    if opt == 1:
        step3 = 1
        HAC_T_opt(fname, CDist, step3, outfname, cenfname)
    elif dbscan == 1:
        DBSCAN_procedure(fname, CDist, outfname, cenfname)
    elif allow == 1:
        HAC_T(fname, CDist, step3, outfname, cenfname, True)
    else:
        HAC_T(fname, CDist, step3, outfname, cenfname, False)

    if showtime == 1:
        end_time = datetime.datetime.now()
        tdelta = (end_time - start_time)
        delta_micro = tdelta.microseconds + tdelta.seconds * 1000000
        delta_ms = delta_micro // 1000
        print("HAC_T (ms)\t" + fname + "\t" + str(delta_ms))

if __name__ == "__main__":
    main()
