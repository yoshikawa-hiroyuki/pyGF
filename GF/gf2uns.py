#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gf2uns : convert FFB/GF files(with non dividing mesh) to LSV Uns files
  read : MESH, FLOW
  write: Index, UnsMesh, UnsData
"""
import sys, os
import struct
import getopt
import GF


def usage0():
    print 'usage: %s [-h|--help]' % os.path.basename(sys.argv[0])
    print '       %s <--mesh|--amesh> meshfile <--data|--adata> datafile \\' \
         % os.path.basename(sys.argv[0])
    print '          [--out outbase] [--order no]'


def outUnm(path, mesh):
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
    
    # open mesh file
    try:
        ofp = open(path, 'wb')
    except:
        return failRet

    # write node-info block
    ofp.write(struct.pack('2i', nNode, nnNode))
    for i in range(nNode):
        ofp.write(struct.pack('i', i))
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
    nEInner = 0

    # write TETRA elem block
    if nTetra > 0:
        ofp.write(struct.pack('iii', 4, nTetra, 0)) # EType, nEInner, nEOverlap
        for i in range(nTetra):
            ofp.write(struct.pack('i', i))
            continue
        for i in range(nElem):
            arr = mesh.dataset[0].data[1].array[i]
            if arr[-1] > 0: continue
            if arr[-4] > 0: continue
            ofp.write(struct.pack('iiii',
                                  arr[0]-1, arr[1]-1, arr[2]-1, arr[3]-1))
            continue

    # write HEXA elem block
    if nHexa > 0 or nPyra > 0:
        nEInner = nHexa + nPyra
        ofp.write(struct.pack('iii', 8, nEInner, 0)) # EType, nEInner, nEOverlap
        for i in range(nEInner):
            ofp.write(struct.pack('i', i + nTetra))
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
    ofp.write(struct.pack('i', 0)) # nPE

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


def outIdx(path, meshPath, dataPath, data, dorder=0):
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
    ofp.write('    <files>1</files>\n')
    ofp.write('  </info>\n')
    ofp.write('  <mesh>\n')
    ofp.write('    <file>%s</file>\n' % meshPath)
    ofp.write('  </mesh>\n')
    ofp.write('  <step index="%d" time="%f">\n' % (stpIndex, stpTime))
    ofp.write('    <file>%s</file>\n' % dataPath)
    ofp.write('  </step>\n')
    ofp.write('</data>\n')
    ofp.write('</LSV_Index>\n')

    ofp.close()
    return 1


if __name__ == '__main__':
    #-------------- ARGUMENTS CHECK --------------
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h',
                                   ['data=', 'adata=', 'mesh=', 'amesh=',
                                    'out=', 'order=', 'help'])
    except getopt.GetoptError:
        usage0()
        sys.exit(1)

    (datafile, meshfile, outbase, order) = (None, None, None, 0)
    (data_bin, mesh_bin) = (True, True)
    for o, a in opts:
        if o in ('-h', '--help'):
            usage0()
            sys.exit(0)
        if o == '--mesh':
            meshfile = a
            mesh_bin = True
            continue
        if o == '--amesh':
            meshfile = a
            mesh_bin = False
            continue
        if o == '--data':
            datafile = a
            data_bin = True
            continue
        if o == '--adata':
            datafile = a
            data_bin = False
            continue
        if o == '--out':
            outbase = a
            continue
        if o == '--order':
            order = int(a)
            continue
        continue

    #-------------- DATA INPUT --------------
    if datafile == None or meshfile == None:
        print('%s: invalid argument.' % sys.argv[0])
        usage0()
        sys.exit(1)

    Mesh = GF.GF_FILE()
    print 'reading mesh file: %s ...' % meshfile,
    sys.stdout.flush()
    if mesh_bin:
        ret = Mesh.read(meshfile)
    else:
        ret = Mesh.read_ascii(meshfile)
    if not ret:
        print('%s: mesh file load failed: %s\n' % (sys.argv[0], meshfile))
        sys.exit(2)
    print 'done'

    Data = GF.GF_FILE()
    print 'reading data file: %s ...' % datafile,
    sys.stdout.flush()
    if data_bin:
        ret = Data.read(datafile)
    else:
        ret = Data.read_ascii(datafile)
    if not ret:
        print('%s: data file load failed: %s\n' % (sys.argv[0], datafile))
        sys.exit(3)
    print 'done'

    #-------------- DATA OUTPUT --------------
    if outbase == None:
        outMesh = 'GFDATA.unm'
        outData = 'GFDATA.und'
        outIndex = 'GFDATA.idx'
    else:
        outMesh = outbase + '.unm'
        outData = outbase + '.und'
        outIndex = outbase + '.idx'

    (nNode, nElem) = outUnm(outMesh, Mesh)
    if nNode < 1 or nElem < 1:
        print('%s: Mesh file output failed: %s\n' % (sys.argv[0], outMesh))
        sys.exit(5)

    if outUnd(outData, nNode, nElem, Mesh, Data, order) == 0:
        print('%s: Data file output failed: %s\n' % (sys.argv[0], outData))
        sys.exit(6)

    if outIdx(outIndex, outMesh, outData, Data, order) == 0:
        print('%s: Index file output failed: %s\n' % (sys.argv[0], outIndex))
        sys.exit(7)

    #-------------- DONE --------------
    sys.exit(0)
