#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gf2vtk : convert FFB/GF files(with non dividing mesh) to VTK files
  read : MESH, FLOW
  write: VTK (Unstructured Grid)
"""
import sys, os
import struct
import getopt
import GF
try:
    import vtk
except:
    print('%s: import vtk failed, VTK may not installed.' % sys.argv[0])
    sys.exit(1)


def usage0():
    print('usage: %s [-h|--help]' % os.path.basename(sys.argv[0]))
    print('       %s <--mesh|--amesh> meshfile <--data|--adata> datafile \\'\
         % os.path.basename(sys.argv[0]))
    print('          [--out outfile.vtk] [--order int]')


def outVTK(path, grid):
    """
    outVTK: write grid data to the specified VTK file
    @param path: path to the VTK file
    @param grid: grid data to write
    """
    uWriter = vtk.vtkUnstructuredGridWriter()
    uWriter.SetInputData(grid)
    uWriter.SetFileName(path)
    try:
        uWriter.Write()
    except:
        return False
    return True


def setupMesh(grid, mesh):
    """
    setupMesh: setup mesh data to the grid data
    @param grid: grid data (vtkUnstructuredGrid)
    @param mesh: mesh data (GL_FILE)
    @returns (#of nodes, #of elems)
    """
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
    if nETypes < 1:
        return failRet

    # set node array
    points = vtk.vtkPoints()
    for i in range(nnNode):
        arr = mesh.dataset[0].data[0].array[i]
        points.InsertNextPoint(arr)
        continue # end of for(i)
    grid.SetPoints(points)
    del points

    # set cell array
    for i in range(nElem):
        arr = mesh.dataset[0].data[1].array[i]
        if arr[-1] > 0: # Hexa
            hex = vtk.vtkHexahedron() 
            hpids = hex.GetPointIds()
            for j in range(8):
                hpids.SetId(j, arr[j]-1)
                continue # end of for(j)
            grid.InsertNextCell(hex.GetCellType(), hex.GetPointIds())
        elif arr[-4] > 0: # Pyramid
            pyr = vtk.vtkPyramid() 
            hpids = pyr.GetPointIds()
            for j in range(5):
                hpids.SetId(j, arr[j]-1)
                continue # end of for(j)
            grid.InsertNextCell(pyr.GetCellType(), pyr.GetPointIds())
        else: # Tetra
            tet = vtk.vtkTetra()
            hpids = tet.GetPointIds()
            for j in range(4):
                ids.SetId(j, arr[j]-1)
                continue # end of for(j)
            grid.InsertNextCell(tet.GetCellType(), tet.GetPointIds())
        continue # end of for(i)
    
    return (nnNode, nTetra + nPyra + nHexa)


def setupData(nNode, nElem, grid, data, dorder=0):
    """
    setupData: setup node/elem data to the grid data
    @param nNode: #of nodes
    @param nElem: #of elems
    @param grid: grid data (vtkUnstructuredGrid)
    @param data: numerical data (GL_FILE)
    @param dorder: the order of data to setup (default=0)
    @returns length of data setup'ed
    """
    if nNode < 1 or nElem < 1: return 0
    if data == None or len(data.dataset) < 1 or len(data.dataset[0].data) < 3:
        return 0
    if dorder < 0 or dorder >= len(data.dataset[0].data) - 2:
        return 0

    Data = data.dataset[0].data[dorder + 2] # 0 is TIME, 1 is STEP
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

    # set node data
    if nND == 1:
        ndatas = vtk.vtkFloatArray()
        for i in range(nNode):
            ndatas.InsertNextTuple(Data.array[i][0:1])
            continue # end of for(i)
        ndatas.SetName(Data.comment)
        grid.GetPointData().AddArray(ndatas)
        del ndatas
    elif nND == 3:
        ndatas = vtk.vtkFloatArray()
        ndatas.SetNumberOfComponents(3)
        for i in range(nNode):
            ndatas.InsertNextTuple(Data.array[i][0:3])
            continue # end of for(i)
        ndatas.SetName(Data.comment)
        grid.GetPointData().AddArray(ndatas)
        del ndatas

    # set elem data
    if nED ==  1:
        edatas = vtk.vtkFloatArray()
        for i in range(nElem):
            edatas.InsertNextTuple(Data.array[i][0:1])
            continue # end of for(i)
        edatas.SetName(Data.comment)        
        grid.GetCellData().AddArray(edatas)
        del edatas
    elif nED == 3:
        edatas = vtk.vtkFloatArray()
        edatas.SetNumberOfComponents(3)
        for i in range(nElem):
            edatas.InsertNextTuple(Data.array[i][0:3])
            continue # end of for(i)
        edatas.SetName(Data.comment)        
        grid.GetCellData().AddArray(edatas)
        del edatas

    return nND + nED


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
    sys.stdout.write('reading mesh file: %s ...' % meshfile)
    sys.stdout.flush()
    if mesh_bin:
        ret = Mesh.read(meshfile)
    else:
        ret = Mesh.read_ascii(meshfile)
    if not ret:
        print('%s: mesh file load failed: %s\n' % (sys.argv[0], meshfile))
        sys.exit(2)
    print('done')

    Data = GF.GF_FILE()
    sys.stdout.write('reading data file: %s ...' % datafile)
    sys.stdout.flush()
    if data_bin:
        ret = Data.read(datafile)
    else:
        ret = Data.read_ascii(datafile)
    if not ret:
        print('%s: data file load failed: %s\n' % (sys.argv[0], datafile))
        sys.exit(3)
    print('done')

    #-------------- DATA OUTPUT --------------
    if outbase == None:
        outvtk = 'GFDATA.vtk'
    elif outbase.endswith('.vtk'):
        outvtk = outbase
    else:
        outvtk = outbase + '.vtk'

    grid = vtk.vtkUnstructuredGrid()
        
    (nNode, nElem) = setupMesh(grid, Mesh)
    if nNode < 1 or nElem < 1:
        print('%s: Mesh traverse failed.\n' % sys.argv[0])
        sys.exit(5)

    if setupData(nNode, nElem, grid, Data, order) == 0:
        print('%s: Data traverse failed.\n' % sys.argv[0])
        sys.exit(6)

    if outVTK(outvtk, grid) == 0:
        print('%s: vtk file output failed: %s\n' % (sys.argv[0], outvtk))
        sys.exit(7)

    #-------------- DONE --------------
    sys.exit(0)
