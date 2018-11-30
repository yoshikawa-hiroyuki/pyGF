#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gf2lsvPara : convert FFB/GF files(with dividing mesh) to LSV Uns files
  read : MESH.Pnnn, FLOW.Pnnn, DDD
  write: Index, UnsMesh, UnsData
"""
import sys, os
import math
import numpy
import struct
import getopt
import GF


def usage0():
    print 'usage: %s [-h|--help]' % os.path.basename(sys.argv[0])
    print '       %s --ddd dddfile --mesh meshbase --data database' \
        % os.path.basename(sys.argv[0])
    print '       \t\t[--out outbase] [--order dataNo]'


def checkDDD(ddd):
    if ddd == None: return -1
    numDomain = len(ddd.dataset)
    if numDomain < 1: return -1
    for i in range(numDomain):
        if len(ddd.dataset[i].data) < 3:
            return -1
        continue
    return numDomain
    

def outUnm(path, mesh, ddd, dom):
    failRet = (-1, -1)
    if mesh == None or len(mesh.dataset) < 1 or len(mesh.dataset[0].data) < 2:
        return failRet
    NodeLst = mesh.dataset[0].data[0]
    NodeTbl = mesh.dataset[0].data[1]
    nNode = NodeLst.aryNum[0]
    nElem = NodeTbl.aryNum[0]
    if nNode < 1 or nElem < 1:
        return failRet
    nnNode = nNode

    if ddd == None or dom < 0 or len(ddd.dataset) <= dom:
        return failRet
    domain = ddd.dataset[dom]
    if len(domain.data) != 3:
        return failRet
    if domain.data[0].aryNum[0] != nNode or domain.data[1].aryNum[0] != nElem:
        return failRet
    globalNodeLst = domain.data[0].array
    globalElemLst = domain.data[1].array
    boundNodeLst = numpy.unique(domain.data[2].array[:,0])
    nBN = len(boundNodeLst)
    nNode = nnNode - nBN
    
    # open mesh file
    try:
        ofp = open(path, 'wb')
    except:
        return failRet

    # write node-info block
    ofp.write(struct.pack('2i', nNode, nnNode))
    for i in range(nnNode):
        ofp.write(struct.pack('i', globalNodeLst[i]-1))
        continue

    # scan elem info
    (nTetra, nPyra, nHexa) = (0, 0, 0)
    for i in range(nElem):
        if mesh.dataset[0].data[1].array[i][-1] > 0:
            nHexa = nHexa + 1
        elif mesh.dataset[0].data[1].array[i][-4] > 0:
            nPyra = nPyra + 1
        else:
            nTetra = nTetra + 1
        continue
    nETypes = 0
    if nHexa > 0 or nPyra > 0: nETypes = nETypes + 1
    if nTetra > 0: nETypes = nETypes + 1

    # write elem-info block
    ofp.write(struct.pack('i', nETypes))

    # write TETRA elem block
    if nTetra > 0:
        boundElemLst = []
        for i in range(nElem):
            arr = mesh.dataset[0].data[1].array[i]
            if arr[-4] > 0: continue
            for j in arr[0:4]:
                if j in boundNodeLst:
                    boundElemLst = boundElemLst + [i+1,]
                    break
                continue # end of for(j)
            continue # end of for(i)
        nEOverlap = len(boundElemLst)
        nEInner = nTetra - nEOverlap

        ofp.write(struct.pack('iii', 4, nEInner, nEOverlap)) # EType = 4

        for i in range(nElem):
            arr = mesh.dataset[0].data[1].array[i]
            if arr[-4] > 0: continue
            ofp.write(struct.pack('i', globalElemLst[i]-1))
            continue

        for i in range(nElem):
            arr = mesh.dataset[0].data[1].array[i]
            if arr[-4] > 0: continue
            ofp.write(struct.pack('iiii',
                                  arr[0]-1, arr[1]-1, arr[2]-1, arr[3]-1))
            continue

    # write HEXA elem block
    if nHexa > 0 or nPyra > 0:
        nEHP = nHexa + nPyra
        boundElemLst = []
        for i in range(nElem):
            arr = mesh.dataset[0].data[1].array[i]
            if arr[-4] == 0: continue
            for j in arr[:]:
                if j == 0: break
                if j in boundNodeLst:
                    boundElemLst = boundElemLst + [i+1,]
                    break
                continue # end of for(j)
            continue # end of for(i)
        nEOverlap = len(boundElemLst)
        nEInner = nEHP - nEOverlap

        ofp.write(struct.pack('iii', 8, nEInner, nEOverlap)) # EType = 8

        for i in range(nElem):
            arr = mesh.dataset[0].data[1].array[i]
            if arr[-4] == 0: continue
            ofp.write(struct.pack('i', globalElemLst[i]-1))
            continue

        for i in range(nElem):
            arr = mesh.dataset[0].data[1].array[i]
            if arr[-4] == 0: continue
            if arr[-1] == 0: # Pyramid
                ofp.write(struct.pack('8i',
                                      arr[0]-1, arr[1]-1, arr[2]-1, arr[3]-1,
                                      arr[4]-1, arr[4]-1, arr[4]-1, arr[4]-1 ))
                                      #arr[1]-1, arr[2]-1, arr[3]-1, arr[4]-1,
                                      #arr[0]-1, arr[0]-1, arr[0]-1, arr[0]-1 ))
                continue
            ofp.write(struct.pack('8i', arr[0]-1, arr[1]-1, arr[2]-1, arr[3]-1,
                                  arr[4]-1, arr[5]-1, arr[6]-1, arr[7]-1 ))
            continue

    # write Ngrp block
    ofp.write(struct.pack('i', 0)) # nNgrp

    # write Egrp block
    ofp.write(struct.pack('i', 0)) # nEgrp

    # write Sgrp block
    ofp.write(struct.pack('i', 0)) # nSgrp

    # write Comm block
    PELst = numpy.unique(domain.data[2].array[:,1])
    nPE = len(PELst)
    ofp.write(struct.pack('i', nPE))
    if nPE > 0:
        PENodeLst = {}
        for i in range(nPE):
            ofp.write(struct.pack('i', PELst[i]-1)) # PEid
            PENodeLst[PELst[i]] = []
            continue
        for i in range(domain.data[2].aryNum[0]):
            PENodeLst[domain.data[2].array[i][1]].append( \
                domain.data[2].array[i][0])
            continue
        for i in PENodeLst:
            ofp.write(struct.pack('i', len(PENodeLst[i]))) # PE_nN
            continue
        for i in PENodeLst:
            for j in PENodeLst[i]:
                ofp.write(struct.pack('i', j-1)) # PE_Nid
                continue
            continue

    # write xyz block
    ofp.write(struct.pack('i', nnNode))
    ofp.write(struct.pack('i', 3)) # nD
    for i in range(nnNode):
        arr = mesh.dataset[0].data[0].array[i]
        ofp.write(struct.pack('ddd', arr[0], arr[1], arr[2]))
        continue

    ofp.close()
    return (nnNode, nTetra + nPyra + nHexa)


def outUnd(path, nNode, nElem, mesh, data, dorder=0):
    if nNode < 1 or nElem < 1: return 0
    if mesh == None or len(mesh.dataset) < 1 or len(mesh.dataset[0].data) < 2:
        return 0
    if data == None or len(data.dataset) < 1 or len(data.dataset[0].data) < 3:
        return 0
    if dorder < 0 or dorder >= len(data.dataset[0].data) - 2:
        return 0

    Etbl = mesh.dataset[0].data[1]
    Data = data.dataset[0].data[dorder + 2]
    (nND, nED) = (0, 0)
    NodeData = True
    if Data.keyword[-1] == 'E':
        NodeData = False

    if NodeData:
        nnNode = Data.aryNum[0]
        if nNode != nnNode:
            return 0
        nND = Data.aryNum[1]
        if nND != 1 and nND != 3:
            return 0
    else:
        nnElem = Data.aryNum[0]
        if nElem < nnElem:
            return 0
        nED = Data.aryNum[1]
        if nED != 1 and nED != 3:
            return 0

    if nND == 0 and nED == 0:
        return 0

    # open data file
    try:
        ofp = open(path, 'wb')
    except:
        return 0

    # write node data block
    ofp.write(struct.pack('2i', nNode, nND))
    if nND == 1:
        for i in range(nNode):
            ofp.write(struct.pack('d', Data.array[i][0]))
            continue
    elif nND == 3:
        for i in range(nNode):
            ofp.write(struct.pack('ddd', Data.array[i][0],
                                  Data.array[i][1], Data.array[i][2]))
            continue

    # write elem data block
    ofp.write(struct.pack('2i', nElem, nED))
    if nED > 0:
        (nTetra, nPyra, nHexa) = (0, 0, 0)
        for i in range(nnElem):
            if Etbl.array[i][-1] > 0:
                nHexa = nHexa + 1
            elif Etbl.array[i][-4] > 0:
                nPyra = nPyra + 1
            else:
                nTetra = nTetra + 1
            continue

        # write TETRA elem block
        if nTetra > 0:
            for i in range(nnElem):
                arr = Etbl.array[i]
                if arr[-4] > 0: continue
                for j in range(nED):
                    ofp.write(struct.pack('d', Data.array[i][j]))
                continue

        # write HEXA elem block
        if nHexa > 0 or nPyra > 0:
            for i in range(nnElem):
                arr = Etbl.array[i]
                if arr[-4] == 0: continue
                for j in range(nED):
                    ofp.write(struct.pack('d', Data.array[i][j]))
                continue

    ofp.close()
    return nND - nED


def outIdx(path, meshPathes, dataPathes, data, dorder=0):
    if len(meshPathes) != len(dataPathes):
        return 0
    if data == None or len(data.dataset) < 1 or len(data.dataset[0].data) < 3:
        return 0
    if dorder < 0 or dorder >= len(data.dataset[0].data) - 2:
        return 0

    Data = data.dataset[0].data[dorder + 2]
    (nND, nED) = (0, 0)
    NodeData = True
    if Data.keyword[-1] == 'E':
        NodeData = False

    if NodeData:
        nnNode = Data.aryNum[0]
        if nNode != nnNode:
            return 0
        nND = Data.aryNum[1]
        if nND != 1 and nND != 3:
            return 0
    else:
        nnElem = Data.aryNum[0]
        if nElem < nnElem:
            return 0
        nED = Data.aryNum[1]
        if nED != 1 and nED != 3:
            return 0
    if nND == 0 and nED == 0:
        return 0

    stpIndex = 0
    stpTime = 0.0
    for i in range(2):
        if data.dataset[0].data[i].keyword == '*TIME_PS':
            stpTime = float(data.dataset[0].data[i].array[0][0])
            continue
        if data.dataset[0].data[i].keyword == '*STEP_PS':
            stpTime = int(data.dataset[0].data[i].array[0][0])
            continue
        continue

    # open data file
    try:
        ofp = open(path, 'w')
    except:
        return 0

    # write index data
    ofp.write('<?xml version="1.0" encoding="utf-8"?>\n')
    ofp.write('<LSV_Index>\n')
    ofp.write('<data type="UNS">\n')
    ofp.write('  <info>\n')
    ofp.write('    <ndatas>%d</ndatas>\n' % nND)
    ofp.write('    <edatas>%d</edatas>\n' % nED)
    ofp.write('    <files>%d</files>\n' % len(meshPathes))
    ofp.write('  </info>\n')
    ofp.write('  <mesh>\n')
    for p in meshPathes:
        ofp.write('    <file>%s</file>\n' % p)
    ofp.write('  </mesh>\n')
    ofp.write('  <step index="%d" time="%f">\n' % (stpIndex, stpTime))
    for p in dataPathes:
        ofp.write('    <file>%s</file>\n' % p)
    ofp.write('  </step>\n')
    ofp.write('</data>\n')
    ofp.write('</LSV_Index>\n')

    ofp.close()
    return 1


if __name__ == '__main__':
    #-------------- ARGUMENTS CHECK --------------
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h',
                                   ['ddd=','data=', 'mesh=', 'out=', 'order=', \
                                        'help'])
    except getopt.GetoptError:
        usage0()
        sys.exit(1)

    (dddfile, database, meshbase, outbase, order) = (None, None, None, None, 0)
    for o, a in opts:
        if o in ('-h', '--help'):
            usage0()
            sys.exit(0)
        if o == '--ddd':
            dddfile = a
            continue
        if o == '--mesh':
            meshbase = a
            continue
        if o == '--data':
            database = a
            continue
        if o == '--out':
            outbase = a
            continue
        if o == '--order':
            order = int(a)
            continue
        continue

    #-------------- DATA INPUT --------------
    if dddfile == None or database == None or meshbase == None:
        print('%s: invalid argument.' % sys.argv[0])
        usage0()
        sys.exit(1)

    ddd = GF.GF_FILE()
    print 'reading ddd file: %s ...' % dddfile,
    sys.stdout.flush()
    if not ddd.read(dddfile):
        print('%s: ddd file load failed: %s\n' % (sys.argv[0], dddfile))
        sys.exit(1)
    numDomain = checkDDD(ddd)
    if numDomain < 1:
        print('%s: invalid ddd file specified %s\n' % (sys.argv[0], dddfile))
        sys.exit(1)
    print 'done'

    #-------------- PREPARE INPUT FILENAME --------------
    inMesh = os.popen('ls -1 %s*' % meshbase).read().split()
    inData = os.popen('ls -1 %s*' % database).read().split()
    if len(inMesh) < numDomain or len(inData) < numDomain:
        print('%s: subdomain of DDD and mesh, data file num mismatch\n' \
                  % sys.argv[0])
        sys.exit(4)

    #-------------- DATA CONVERSION --------------
    outMesh = []
    outData = []
    sdo = int(math.ceil(math.log10(numDomain + 0.1)))
    if sdo < 4: sdo = 4
    domFmt = '_%%0%dd' % sdo

    #---- main loop ----
    for sd in range(numDomain):
        if outbase == None:
            outMesh = outMesh + ['GFDATA' + domFmt % sd + '.unm']
            outData = outData + ['GFDATA' + domFmt % sd + '.und']
        else:
            outMesh = outMesh + [outbase + domFmt % sd + '.unm']
            outData = outData + [outbase + domFmt % sd + '.und']

        # read mesh
        meshfile = inMesh[sd]
        Mesh = GF.GF_FILE()
        print 'reading mesh file: %s ...' % meshfile,
        sys.stdout.flush()
        if not Mesh.read(meshfile):
            print('%s: mesh file load failed: %s\n' % (sys.argv[0], meshfile))
            sys.exit(2)
        print 'done'

        # read data
        datafile = inData[sd]
        Data = GF.GF_FILE()
        print 'reading data file: %s ...' % datafile,
        sys.stdout.flush()
        if not Data.read(datafile):
            print('%s: data file load failed: %s\n' % (sys.argv[0], datafile))
            sys.exit(3)
        print 'done'

        # write mesh
        print 'writing mesh file: %s ...' % outMesh[sd],
        sys.stdout.flush()
        (nNode, nElem) = outUnm(outMesh[sd], Mesh, ddd, sd)
        if nNode < 1 or nElem < 1:
            print('%s: Mesh file output failed: %s\n' % \
                      (sys.argv[0], outMesh[sd]))
            sys.exit(5)
        print 'done'

        # write data
        print 'writing data file: %s ...' % outData[sd],
        sys.stdout.flush()
        if outUnd(outData[sd], nNode, nElem, Mesh, Data, order) == 0:
            print('%s: Data file output failed: %s\n' % \
                      (sys.argv[0], outData[sd]))
            sys.exit(6)
        print 'done'

        continue # end of for(sd)
    #---- main loop ----


    #-------------- INDEX OUTPUT --------------
    if outbase == None:
        outIndex = 'GFDATA.idx'
    else:
        outIndex = outbase + '.idx'

    print 'writing index file: %s ...' % outIndex,
    sys.stdout.flush()
    if outIdx(outIndex, outMesh, outData, Data, order) == 0:
        print('%s: Index file output failed: %s\n' % (sys.argv[0], outIndex))
        sys.exit(7)
    print 'done'

    #-------------- DONE --------------
    sys.exit(0)
