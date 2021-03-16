#!/usr/bin/python3
#
# ETS to ADF antenna pattern conversion utility
#
# Copyright 2021 Farrant Consulting Ltd
# CloudRF.com
import csv
import sys
import numpy as np
from scipy.interpolate import make_interp_spline, BSpline
import os
from collections import deque

horizontal = []
vertical = []

# Change me
oem="ACME"
model="OMNI"
limit=90 # db threshold for QC
targetPlane = "Vertical"# Horizontal | Vertical | Total

if len(sys.argv) < 2:
    print("Usage: python3 ets2adf.py {ets.csv}")
    quit()

outdir="adf"
try:
    os.mkdir(outdir)
except:
    pass

def rotate(l, n):
    return l[n:] + l[:n]

def writeADF(oem,model,frequencyMHz,horizontal,vertical):
    filename = oem+"_"+model+"_"+str(frequencyMHz)+"M.adf"
    print(filename)
    vertical = deque(vertical)
    vertical.rotate(90)
    adf = open(outdir+"/"+filename,"w")
    adf.write("REVNUM:,TIA/EIA-804-B\n")
    adf.write("COMNT1:,Standard TIA/EIA Antenna Pattern Data\n")
    adf.write("ANTMAN:,"+oem+"\n")
    adf.write("MODNUM:,"+model+"\n")
    adf.write("DESCR1:,"+str(frequencyMHz)+"MHz\n")
    adf.write("DESCR2:,Made with love at CloudRF.com\n")
    adf.write("DTDATA:,20210316\n")
    adf.write("LOWFRQ:,0\n")
    adf.write("HGHFRQ:,"+str(frequencyMHz)+"\n")
    adf.write("GUNITS:,DBD/DBR\n")
    adf.write("MDGAIN:,0.0\n")
    adf.write("AZWIDT:,360\n")
    adf.write("ELWIDT:,360\n")
    adf.write("CONTYP:,\n")
    adf.write("ATVSWR:,1.5\n")
    adf.write("FRTOBA:,0\n")
    adf.write("ELTILT:,0\n")
    adf.write("MAXPOW:,\n")
    adf.write("ANTLEN:,\n")
    adf.write("ANTWID:,\n")
    adf.write("ANTWGT:,\n")
    adf.write("PATTYP:,Typical\n")
    adf.write("NOFREQ:,1\n")
    adf.write("PATFRE:,"+str(frequencyMHz)+"\n")
    adf.write("NUMCUT:,2\n")
    adf.write("PATCUT:,H\n")
    adf.write("POLARI:,V/V\n")
    adf.write("NUPOIN:,360\n")
    adf.write("FSTLST:,-179,180\n")
    a=-179
    for h in horizontal:
        adf.write(str(a)+","+str(round(h,3))+"\n")
        a+=1
    adf.write("PATCUT:,V\n")
    adf.write("POLARI:,V/V\n")
    adf.write("NUPOIN:,360\n")
    adf.write("FSTLST:,-179,180\n")
    a=-179
    for v in vertical:
        adf.write(str(a)+","+str(round(v,3))+"\n")
        a+=1
    adf.write("ENDFIL:,EOF\n")
    adf.close()

with open(sys.argv[1]) as csvfile:
    # First pass: Find best column and row
    reader = csv.reader(csvfile, delimiter=',')
    bestColumn=0
    bestRow=0
    r=1
    pos=0
    rowZero=0
    rowOneSixFive=-1
    frequencyMHz=0
    count=1
    plane=""
    for row in reader:
        if len(row) >= 2 and targetPlane == row[0]:
            plane=row[0] # Horizontal | Vertical | Total
            print(plane)
        if len(row) > 25:
            if "Azimuth (deg)" in row[2]: # Data columns header
                frequencyMHz=float(row[1])
                rowZero=pos+2 # start here, regardless of polarisation
                rowOneSixFive=pos+13
            if pos >= rowZero and pos <= rowOneSixFive:

                # Wait for 90  then iterate over that row
                if row[2] == '90':
                    for dbm in row[3:27]:
                        horizontal.append(float(dbm))
                if float(row[3]) > limit:
                    print("Bad data on row %d (%s)" % (r,row[3]))
                    quit()

                vertical.append(float(row[3]))
                count+=1

                if len(vertical) == 12: # 0 to 165 degs @ 15 deg sep
                    # mirror image on vertical...
                    p=11
                    while p > -1:
                        vertical.append(vertical[p])
                        p-=1
                    if len(horizontal) != 24 or len(vertical) != 24:
                        print("ERROR! Expected 24 15-deg dB readings per plane: Horizontal values = %d Vertical values = %d" % (len(horizontal),len(vertical)))
                    else:
                        # We have data! Let's interpolate...
                        twentyFour=np.arange(24)
                        threeSixty = np.linspace(np.min(twentyFour), np.max(twentyFour), 360)
                        # Prepare spline thingy
                        hspl = make_interp_spline(twentyFour, horizontal, k=3)
                        # Smooth it over 360 points
                        h_smooth = hspl(threeSixty)

                        # Prepare spline thingy
                        vspl = make_interp_spline(twentyFour,vertical, k=3)
                        # Smooth it over 360 points
                        v_smooth = vspl(threeSixty)

                        # sanity check values...
                        p=0
                        while p < len(h_smooth):
                            if h_smooth[p] > limit or h_smooth[p] < -limit:
                                print("Bad value in h_smooth index %d: %.3f" % (p,h_smooth[p]))
                                quit()
                            if v_smooth[p] > limit or v_smooth[p] < -limit:
                                print("Bad value in v_smooth index %d: %.3f" % (p,v_smooth[p]))
                                quit()
                            p+=1
                        horizontal = []
                        vertical = []
                        writeADF(oem,model,frequencyMHz,h_smooth,v_smooth)

                    vertical = []
                    horizontal = []
        pos+=1
        r+=1
