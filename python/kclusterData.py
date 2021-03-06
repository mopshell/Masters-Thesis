#!/usr/bin/python2
#
# python-mode indent C-c < or C-c >
# python-mode comment/uncomment region M-;
# Note Scipy detrend is same as doing a remove mean and then detrend
# Detrend demean taper rotate rename save

# This performs the kmeans clustering algorithm on
# SAC data in a given station folder. The program opens
# Each folder and picks out a sac


###########################################################################
# IMPORTS
###########################################################################
import os, re, time, shutil, sys, json, argparse
from preprocessor import renameEvent, is_number
from collections import defaultdict
import numpy as np
from math import cos, acos, pi, sin, atan2, sqrt
import matplotlib.pyplot as plt
from obspy.core import read
import scipy.io
from random import randint
from mpl_toolkits.basemap import Basemap
from sklearn.cluster import KMeans

def vectorize(latlon):
    ''' Takes lat and long and spits out 3D vects'''
    vects = np.zeros( (len(latlon), 3) )
    rads = latlon * pi / 180      #convert to radians
    for ind, obs in enumerate(rads):
        vects[ind] = [cos(obs[0]) * cos(obs[1]) ,
                      cos(obs[0]) * sin(obs[1]) ,
                      sin(obs[0]) ]
    return vects

def assignVect2Cluster(vects, clusters):
   '''This calculates distances between vects and array of clusters
   producing an array of distances, each row for obs and each col
   for particular cluster, than we choose index of min dist'''
   members = np.dot(vects, clusters.T).argmin(axis = 1)
   return members

def moveClusters(vects, clusters, members):
    ''' selects the vects belonging into a cluster, sums along the
    the components and divides by length to get mean vect component
    and sets the cluster at this new mean'''
    for ind in range( len(clusters) ):
        clusters[ind] = vects[members == ind].sum(axis = 0) / len(vects)
    return clusters

def devectorize(vects):
    latlon = np.zeros( (len(vects) , 2) )
    for ind, v in enumerate(vects):
        latlon[ind] = [ atan2( v[2], sqrt( v[0]**2 + v[1]**2) ) ,
                   atan2( v[1], v[0] ) ]
    return latlon * 180/pi



def clusterEvents(stdir, k, showmap = True):
    reg1 = re.compile(r'^stack_P.sac')
    events = os.listdir(stdir)
    events = filter(is_number,events)
    evlist = []
    evdict = {}
    data = np.zeros( (len(events), 2) )

    ind = 0
    for event in events:
        files = os.listdir( os.path.join(stdir, event) )
        for fs in files:
            if reg1.match(fs):
                st = read( os.path.join(stdir, event, fs) )
                evla = float(st[0].stats.sac['evla'])
                evlo = float(st[0].stats.sac['evlo'])
                data[ind] = [ evla, evlo ]
                evlist.append(event)
                ind += 1
                continue

    # Default to two clusters, one around japan the other
    # around Chile.
    vects = vectorize(data)

    if k == 3:
        initguess = vectorize(np.array( [ [58., 149.],
                                          [-7., -74.],
                                          [37., 11.]
                                          ] ))
    else:
        initguess = "k-means++"
    # Perform Kmeans
    kmeans = KMeans(init = initguess, k = k, n_init = 10).fit( vects )
    members = kmeans.labels_

    # Build results
    clusters = devectorize( kmeans.cluster_centers_ )
    cldict = {}

    for ind, ev in enumerate(evlist):
        evdict[ev] = members[ind]

    for ind, cluster in enumerate(clusters):
        cldict[ind] = list(cluster)

    if showmap:
        bmap = Basemap(projection = 'robin', lon_0 = -80)
        bmap.fillcontinents(color = '#cc9966', lake_color = '#99ffff')
        bmap.drawmapboundary(fill_color='0.3')
        bmap.drawparallels(np.arange(-90.,120.,30.))
        bmap.drawmeridians(np.arange(0.,420.,60.))

        x1, y1 = bmap( data[:,1], data[:,0] )
        x2, y2 = bmap( clusters[:,1], clusters[:,0] )

        p2 = []
        clr = ['g','b','r','k','m']
        for i in range( len(clusters) ):
            bmap.scatter(x1[members == i], y1[members == i], c = clr[i], marker = 'o')
            p2.append(bmap.scatter(x2[i],y2[i], c = clr[i], marker = '+', s = 120, linewidths = 2, zorder = 12))

        legstr = [ "Cluster " + str(i) for i in range(k) ]
        plt.legend(p2, legstr)
        plt.show()

    return evdict, cldict


def clusterStations(stdict, k, showmap = True):
    ''' Clusters stations in k groups and outputs a dictionary
    of cluster groups, their centre point and an array of stations'''

    data = np.zeros( (len(stdict), 2) )
    stations = []

    # Build data
    for ind, st in enumerate(stdict.keys()):
        data[ind] = [ stdict[st]['lat'], stdict[st]['lon'] ]
        stations.append(st)

    vects = vectorize(data)

    # Perform Kmeans
    kmeans = KMeans(init='random', k = k, n_init = 10).fit( vects )
    members = kmeans.labels_

    # Build results
    clusters = devectorize( kmeans.cluster_centers_ )
    cldict = {}

    for ind, cluster in enumerate(clusters):
        stns = [x for i, x in enumerate(stations) if members[i] == ind]
        cldict[ind] = {'center': list(cluster), 'stations': stns }

    if showmap:
        m = Basemap(width = 6000000,height = 5000000, projection='stere',
                    resolution='c',lat_1=73.,lat_2=68,lat_0=63,lon_0 = -90.)

        # fill continents, set lake color same as ocean color.
        m.fillcontinents(color = '#cc9966', lake_color = '#99ffff')
        m.drawmapboundary(fill_color='0.3')
        #m.fillcontinents(color='coral',lake_color='aqua')
        #m.drawmapboundary(fill_color='aqua')
        # draw parallels and meridians.
        # label parallels on right and top
        # meridians on bottom and left
        parallels = np.arange(0.,81,10.)
        # labels = [left,right,top,bottom]
        m.drawparallels(parallels,labels=[False,True,True,False])
        meridians = np.arange(10.,351.,20.)
        m.drawmeridians(meridians,labels=[True,False,False,True])

        x1, y1 = m( data[:,1], data[:,0] )
        x2, y2 = m( clusters[:,1], clusters[:,0] )

        p2 = []
        clr = ['b','g','r','c','m','y','k','w']
        for i in range( len(clusters) ):
            m.scatter(x1[members == i], y1[members == i], c = clr[i], marker = 'o',  zorder= 10)
            p2.append(m.scatter(x2[i],y2[i], c = clr[i], marker = '+', s = 120, linewidths = 2, zorder = 12))

        legstr = [ "Cluster " + str(i) for i in range(k) ]
        plt.legend(p2, legstr)
        #plt.ion()
        plt.show()

    return cldict

def printClusters(clusterd):
    for key, value in clusterd.items():
        print "Centroid:", clusterd[key]["center"]
        for station in clusterd[key]["stations"]:
            print station

if __name__== '__main__' :

    dbfile = os.environ['HOME']+'/thesis/data/stations.json'
    stdict = json.loads( open(dbfile).read() )
    stndir = "/media/TerraS/CN"

    # Create top-level parser
    parser = argparse.ArgumentParser(description = "Cluster stations or events around a cluster lon/lat")
    group = parser.add_mutually_exclusive_group()
    # Create query parser
    group.add_argument('-s','--stations', nargs = '?', const = True,
                        help = "Cluster stations in first argument or those piped in.")
    group.add_argument('-e','--events', nargs = '?', const = True,
                        help = "Cluster events with given station or piped in stations. -e <station> <station>")
    parser.add_argument('-n','--number', nargs = 1, type = int,
                        help = "Set number of clusters. Default is 2")
    parser.add_argument('-m','--map', action = "store_true",
                        help = "Show map of clustered events")
    parser.add_argument('-p','--printc', action = "store_true",
                        help = "Print list of clusters and members")
    parser.add_argument('-w','--write', action = "store_true",
                        help = "Write event clusters to SAC files")


    args = parser.parse_args()

    if not args.number:
        # Default behaviour
        args.number = [2]

    if args.stations:
        stations = []
        # trick to seperate a newline or space seperated list. Always returns list.
        # Insert stations at beginning of arg list matching case where stations are included after flag
        if not sys.stdin.isatty():
            stations =  re.findall(r'\w+', sys.stdin.read() )
        else:
            stations.append(args.stations)

        stnd = {k:v for k,v in stdict.items() if k in stations[0]}
        clusterd = clusterStations(stnd, args.number[0], showmap = args.map)
        if args.printc:
            printClusters(clusterd)

    if args.events:
        stations = []
        if not sys.stdin.isatty():
            stations =  re.findall(r'\w+', sys.stdin.read() )
        else:
            stations.append(args.events)

        for stn in stations:
            print stn
            evdict, cldict = clusterEvents(os.path.join(stndir,stn), args.number[0], showmap = args.map)
            if args.printc:
                for key in cldict.keys():
                    print key, ":", cldict[key]
                for key in evdict.keys():
                    print key, ":", evdict[key]

            if args.write:
                reg2 = re.compile(r'^stack_(\w)\.sac')
                for event in evdict.keys():
                    files = os.listdir( os.path.join(stndir, stn, event) )
                    for fs in files:
                        if reg2.match(fs):
                            st = read( os.path.join(stndir, stn, event, fs) )
                            st[0].stats.sac['user9'] = evdict[event]
                            st[0].stats.sac['kt9'] = "ClusterFlag"
                            st[0].write(os.path.join(stndir, stn, event, fs), format = 'SAC')
                            continue

