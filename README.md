# pyGF
Python interface for GF file of FrontFlow/Blue,
and utils for converting GF to LSV-Uns/VTK format.

## Install
  ```
  sudo python setup.py install
  ```
or
  ```
  python setup.py install --home=~ ...
  ```

## Usage of GF module
```
# import GF module
from GF import GF

# read MESH file
mesh = GF.GF_FILE()
mesh.read('MESH')
# Node information is stored in mesh.dataset[0].data[0]
print(mesh.dataset[0].data[0])
->GF_DATA(type=FLT, keyword="*GRID_3D", comment="GRID COORDINATES (3-D)", num=70785, num2=3)
print(mesh.dataset[0].data[0].array) # Node coordinates
->[[0.         0.         0.        ]
   [0.1        0.         0.        ]
   ...
   [6.4000001  3.20000005 3.20000005]]
# Elem information is stored in mesh.dataset[0].data[1]
print(mesh.dataset[0].data[1])
->GF_DATA(type=INT, keyword="*NODE_3D", comment="NODE TABLE (3-D)", num=65536, num2=8)
print(mesh.dataset[0].data[1].array) # Elem tables
->[[   1    2   67   66 2146 2147 2212 2211]
   [   2    3   68   67 2147 2148 2213 2212]
   ...
   [68574 68575 68640 68639 70719 70720 70785 70784]]

# read FLOW file
data = GF.GF_FILE()
data.read('FLOW')
# Data records stored in data.dataset[0].data[i],
#  i=0: TIME, i=1: STEP, i=2...: Node/Elem Data
print(data.dataset[0].data[2])
->GF_DATA(type=FLT, keyword="*VELO_3D", comment="FLOW VELOCITY AT NODES (3-D)", num=70785, num2=3)
print(data.dataset[0].data[2].array) # The first data component (vector data at Nodes)
->[[0. 0. 0.]
   [1. 0. 0.]
   ...
   [0. 0. 0.]]
print(data.dataset[0].data[3])
->GF_DATA(type=FLT, keyword="*PRES_3E", comment="PRESSURE AT ELEMENTS (3-D)", num=65536, num2=1)
print(data.dataset[0].data[3].array) # The second data component (scalar data at Elems)
->[[0.054708  ]
   [0.04337496]
   ...
   [0.0005297 ]]
```

## Usage of VTK converter
```
python gf2vtk.py <--mesh|--amesh> meshfile <--data|--adata> datafile \
         [--out outfile.vtk] [--order int]

options:
  --mesh meshfile
    specify MESH file (binary), this or --amesh is required
  --amesh meshfile
    specify MESH file (ascii), this or --mesh is required
  --data datafile
    specify DATA file (binary), this or --adata is required
  --adata datafile
    specify DATA file (ascii), this or --data is required
  --out outfile.vtk
    specify the output file path, this is optional(default is 'GFDATA.vtk')
  --order int
    specify the data component index to convert, this is optional(default is 0)
```

## References
 * <http://www.cenav.org/kdb/?page_id=316>
 * <http://www.ciss.iis.u-tokyo.ac.jp/rss21/theme/multi/fluid/fluid_softwareinfo.html>

## Author
  YOSHIKAWA Hiroyuki, FUJITSU LTD.
