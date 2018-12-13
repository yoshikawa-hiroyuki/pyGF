#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GF File representation for FFB
"""
import sys
import struct
import numpy

INT_ARY_TYPE = int
FLT_ARY_TYPE = float

class GF_DATA(object):
    """
    DATA record of GF File
      aryType: array type (INT|FLT)
      keyword: keyword string ("*xxxxxxx")
      comment: comment string ("xxxxxxxx")
      aryNum : (num, num2)
      array  : 2D array of data
    """
    def __init__(self):
        self.aryType = INT_ARY_TYPE
        self.keyword = 'x' * 8
        self.comment = 'x' * 30
        self.aryNum = [0, 0] # num, num2
        self.array = numpy.array(0, dtype=self.aryType)
        return

    def __str__(self):
        r = 'GF_DATA(type='
        if self.aryType == INT_ARY_TYPE:
            r = r + 'INT'
        elif self.aryType == FLT_ARY_TYPE:
            r = r + 'FLT'
        else:
            r = r + 'INVALID'
        r = r + ', keyword="' + self.keyword.strip() + '"'
        r = r + ', comment="' + self.comment.strip() + '"'
        r = r + ', num=%d' % self.aryNum[0]
        r = r + ', num2=%d' % self.aryNum[1] + ')'
        return r

    def setType(self, atp):
        """
        set data type.
          atp: INT_ARY_TYPE or FLT_ARY_TYPE
        """
        if atp != INT_ARY_TYPE and atp != FLT_ARY_TYPE:
            return False
        if self.aryType == atp:
            return True
        self.aryType = atp
        self.array = numpy.array(0, dtype=self.aryType)
        if self.aryNum[0] > 0 and self.aryNum[1] > 0:
            self.array.resize(self.aryNum)
        return True

    def setNums(self, num, num2):
        """
        set array size of data as num and num2
        """
        if num == self.aryNum[0] and num2 == self.aryNum[1]:
            return True
        if num < 1 or num2 < 1:
            self.aryNum[0] = 0; self.aryNum[1] = 0
            self.array = numpy.array(0, dtype=self.aryType)
            return True
        self.aryNum[0] = num
        self.aryNum[1] = num2
        self.array.resize(self.aryNum)
        return True

    def read(self, ifp, ibo = '='):
        """
        read DATA record from binary GF file
          ifp: opened binary GF file
          ibo: byte order, '<' as little-endian, '>' as big-endian,
               '=' as system byte order.
        """
        if ifp is None: return False
        self.setNums(0, 0)
        fpos = ifp.tell()

        # read array_type_header (8, "#ARY_TYP", 8)
        try:
            buff = struct.unpack(ibo+'i8si', ifp.read(16))
        except:
            try:
                ifp.seek(fpos)
            except:
                pass
            return False
        if buff[0] != 8 or buff[2] != 8:
            try:
                ifp.seek(fpos)
            except:
                pass
            return False
        if buff[1] == '#FLT_ARY':
            if not self.setType(FLT_ARY_TYPE):
                try:
                    ifp.seek(fpos)
                except:
                    pass
                return False
        elif buff[1] == '#INT_ARY':
            if not self.setType(INT_ARY_TYPE):
                try:
                    ifp.seek(fpos)
                except:
                    pass
                return False
        else:
            try:
                ifp.seek(fpos)
            except:
                pass
            return False

        # read keyword (8, "xxxxxxxx", 8)
        try:
            buff = struct.unpack(ibo+'i8si', ifp.read(16))
        except:
            return False
        if buff[0] != 8 or buff[2] != 8: return False
        self.keyword = buff[1]

        # read comment (30, "xxxxxxxx...", 30)
        try:
            buff = struct.unpack(ibo+'i30si', ifp.read(38))
        except:
            return False
        if buff[0] != 30 or buff[2] != 30: return False
        self.comment = buff[1]

        # read num2, num (8, num2, num, 8)
        try:
            buff = struct.unpack(ibo+'iiii', ifp.read(16))
        except:
            return False
        if buff[0] != 8 or buff[3] != 8: return False
        if not self.setNums(buff[2], buff[1]): # args are (num, num2)
            return False

        # read data (sz, data, sz), sz = 4 * num2 * num
        try:
            buff = struct.unpack(ibo+'i', ifp.read(4))
        except:
            return False
        if buff[0] != 4 * self.aryNum[0] * self.aryNum[1]:
            return False
        if self.aryType == INT_ARY_TYPE:
            fmt = ibo+'%di' % self.aryNum[1]
        else:
            fmt = ibo+'%df' % self.aryNum[1]
        sz = 4 * self.aryNum[1]
        try:
            for i in range(self.aryNum[0]):
                buff = struct.unpack(fmt, ifp.read(sz))
                self.array[i][:] = buff[:]
                continue
        except:
            return False
        try:
            buff = struct.unpack(ibo+'i', ifp.read(4))
        except:
            return False

        return True

    def read_ascii(self, ifp):
        """
        read DATA record from ascii GF file
          ifp: opened ascii GF file
        """
        if ifp is None: return False
        self.setNums(0, 0)
        fpos = ifp.tell()

        # read array_type_header ("#ARY_TYP")
        try:
            line = ifp.readline()
        except:
            return False
        if line.startswith('#FLT_ARY'):
            if not self.setType(FLT_ARY_TYPE):
                try:
                    ifp.seek(fpos)
                except:
                    pass
                return False
        elif line.startswith('#INT_ARY'):
            if not self.setType(INT_ARY_TYPE):
                try:
                    ifp.seek(fpos)
                except:
                    pass
                return False
        else:
            try:
                ifp.seek(fpos)
            except:
                pass
            return False

        # read keyword ("xxxxxxxx")
        try:
           line = ifp.readline()
        except:
            return False
        self.keyword = line.rstrip()

        # read comment ("xxxxxxxx...")
        try:
            line = ifp.readline()
        except:
            return False
        self.comment = line.rstrip()

        # read num2, num (num2, num)
        try:
            line = ifp.readline()
        except:
            return False
        buff = line.split()
        if len(buff) < 2:
            return False
        if not self.setNums(int(buff[1]), int(buff[0])): # args are (num, num2)
            return False

        # read data, #of data = num2 * num
        sz = self.aryNum[0] * self.aryNum[1]
        try:
            line = ifp.readline()
        except:
            return False
        if line[0] == '#':
            return False
        buff = line.rstrip()
        while ( True ):
            fpos2 = ifp.tell()
            try:
                line = ifp.readline()
            except:
                break
            if line[0] == '#':
                ifp.seek(fpos2)
                break
            buff = buff + line.rstrip()
            continue
        buff = buff.split()
        if len(buff) < sz:
            return False
        if self.aryType == FLT_ARY_TYPE:
            for i in range(self.aryNum[0]):
                for j in range(self.aryNum[1]):
                    self.array[i][j] = float(buff[i*self.aryNum[1] + j])
        elif self.aryType == INT_ARY_TYPE:
            for i in range(self.aryNum[0]):
                for j in range(self.aryNum[1]):
                    self.array[i][j] = int(buff[i*self.aryNum[1] + j])
        return True

    def write(self, ofp, obo = '='):
        """
        write DATA record to binary GF file
          ifp: opened binary GF file
          obo: byte order, '<' as little-endian, '>' as big-endian,
               '=' as system byte order.
        """
        if ofp is None: return False
        if self.aryNum[0] < 1 or self.aryNum[1] < 1:
            return False

        # write header
        sz = 8
        try:
            if self.aryType == INT_ARY_TYPE:
                ofp.write(struct.pack(obo+'i8si', sz, '#INT_ARY', sz))
            elif self.aryType == FLT_ARY_TYPE:
                ofp.write(struct.pack(obo+'i8si', sz, '#FLT_ARY', sz))
            else:
                return False
        except:
            return False

        # write keyword
        sz = 8
        try:
            ofp.write(struct.pack(obo+'i8si', sz, self.keyword, sz))
        except:
            return False

        # write comment
        sz = 30
        try:
            ofp.write(struct.pack(obo+'i30si', sz, self.comment, sz))
        except:
            return False

        # write num2, num
        sz = 8
        try:
            ofp.write(struct.pack(obo+'iiii',
                                  sz, self.aryNum[1], self.aryNum[0], sz))
        except:
            return False

        # write data
        sz = 4 * self.aryNum[1] * self.aryNum[0]
        try:
            ofp.write(struct.pack(obo+'i', sz))
        except:
            return False
        
        if self.aryType == INT_ARY_TYPE:
            fmt = obo+'i'
        else:
            fmt = obo+'f'
        try:
            for i in range(self.aryNum[0]):
                for j in range(self.aryNum[1]):
                    ofp.write(struct.pack(fmt, self.array[i][j]))
                    continue
                continue
        except:
            return False

        try:
            ofp.write(struct.pack(obo+'i', sz))
        except:
            return False

        return True


class GF_DATASET(object):
    """
    DATASET record of GF File
      comment: array of comment string (60 characters each)
      data:    array of GF_DATA
    """
    def __init__(self):
        self.comment = []
        self.data = []
        return

    def __str__(self):
        if len(self.comment) > 0:
            r = 'GF_DATASET("%s", #of DATA=%d)' % \
                (self.comment[0].strip(), len(self.data))
        else:
            r = 'GF_DATASET(#of DATA=%d)' % len(self.data) 
        return r

    def read(self, ifp, ibo = '='):
        """
        read DATASET record from binary GF file
          ifp: opened binary GF file
          ibo: byte order, '<' as little-endian, '>' as big-endian,
               '=' as system byte order.
        """
        if ifp is None: return False
        self.comment = []
        self.data = []
        fpos = ifp.tell()

        # read header (8, "#NEW_SET", 8)
        try:
            buff = struct.unpack(ibo+'i8si', ifp.read(16))
        except:
            try:
                ifp.seek(fpos)
            except:
                pass
            return False
        if buff[0] != 8 or buff[2] != 8:
            try:
                ifp.seek(fpos)
            except:
                pass
            return False
        if buff[1] != '#NEW_SET':
            try:
                ifp.seek(fpos)
            except:
                pass
            return False

        # read size of comment list (4, n, 4)
        try:
            buff = struct.unpack(ibo+'iii', ifp.read(12))
        except:
            return False
        if buff[0] != 4 or buff[2] != 4: return False
        ncl = buff[1]

        # read comment list (60, "xxx...", 60) * ncl
        for i in range(ncl):
            try:
                buff = struct.unpack(ibo+'i60si', ifp.read(68))
            except:
                return False
            self.comment = self.comment + [buff[1],]
            continue

        # read data list
        data = GF_DATA()
        while ( data.read(ifp, ibo) ):
            self.data = self.data + [data,]
            data = GF_DATA()
            continue

        if len(self.data) < 1:
            return False
        return True

    def read_ascii(self, ifp):
        """
        read DATASET record from ascii GF file
          ifp: opened ascii GF file
        """
        if ifp is None: return False
        self.comment = []
        self.data = []
        fpos = ifp.tell()

        # read header ("#NEW_SET")
        try:
            line = ifp.readline()
        except:
            return False
        if not line.startswith('#NEW_SET'):
            try:
                ifp.seek(fpos)
            except:
                pass
            return False

        # read size of comment list (n)
        try:
            line = ifp.readline()
        except:
            return False
        buff = line.split()
        if len(buff) < 1:
            return False
        ncl = int(buff[0])

        # read comment list ("xxx...") * ncl
        for i in range(ncl):
            try:
                line = ifp.readline()
            except:
                return False
            self.comment.append( line.rstrip() )
            continue

        # read data list
        data = GF_DATA()
        while ( data.read_ascii(ifp) ):
            self.data = self.data + [data,]
            data = GF_DATA()
            continue

        if len(self.data) < 1:
            return False
        return True


    def write(self, ofp, obo = '='):
        """
        write DATASET record to binary GF file
          ifp: opened binary GF file
          obo: byte order, '<' as little-endian, '>' as big-endian,
               '=' as system byte order.
        """
        if ofp is None: return False
        if len(self.data) < 1:
            return False

        # write header
        sz = 8
        try:
            ofp.write(struct.pack(obo+'i8si', sz, '#NEW_SET', sz))
        except:
            return False

        # write size of comment list
        sz = 4
        try:
            ofp.write(struct.pack(obo+'iii', sz, len(self.comment), sz))
        except:
            return False

        # write comment list
        for i in range(len(self.comment)):
            try:
                ofp.write(struct.pack(obo+'i60si', sz, self.comment[i], sz))
            except:
                return False
            continue

        # write data list
        for i in range(len(self.data)):
            if not self.data[i].write(ofp, obo):
                return False
            continue

        return True


class GF_FILE(object):
    """
    GF File representation
      fileType: file type keyword ("#U_GF_XX" or "#A_GF_XX")
      comment:  array of comment string (60 characters each)
      dataset:  array of GF_DATASET
    """
    def __init__(self):
        self.fileType = ''
        self.comment = []
        self.dataset = []
        return

    def __str__(self):
        if len(self.comment) > 0:
            r = 'GF_FILE("%s", type=%s, #of DATASET=%d)' % \
                (self.comment[0].strip(), self.fileType, len(self.dataset))
        else:
            r = 'GF_FILE(type=%s, #of DATASET=%d)' % \
                (self.fileType, len(self.dataset))
        return r
    
    def read(self, path):
        """
        read from a binary GF file
          path: path of the binary GF file
        """
        try:
            ifp = open(path, 'rb')
        except:
            return False

        self.fileType = ''
        self.comment = []
        self.dataset = []
        ibo = '<' # byte order

        # read header (8, "#U_GF_XX", 8)
        try:
            header = ifp.read(16)
        except:
            ifp.close()
            return False
        buff = struct.unpack(ibo+'i8si', header)
        if buff[0] != 8:
            ibo = '>'
            buff = struct.unpack(ibo+'i8si', header)
            if buff[0] != 8:
                ifp.close()
                return False
        if buff[2] != 8:
            ifp.close()
            return False
        self.fileType = buff[1]

        # read size of comment list (4, n, 4)
        try:
            buff = struct.unpack(ibo+'iii', ifp.read(12))
        except:
            ifp.close()
            return False
        if buff[0] != 4 or buff[2] != 4:
            ifp.close()
            return False
        ncl = buff[1]

        # read comment list (60, "xxx...", 60) * ncl
        for i in range(ncl):
            try:
                buff = struct.unpack(ibo+'i60si', ifp.read(68))
            except:
                ifp.close()
                return False
            self.comment = self.comment + [buff[1],]
            continue

        # read dataset list
        dataset = GF_DATASET()
        while ( dataset.read(ifp, ibo) ):
            self.dataset = self.dataset + [dataset,]
            dataset = GF_DATASET()
            continue

        ifp.close()
        if len(self.dataset) < 1:
            return False
        return True

    def read_ascii(self, path):
        """
        read from an ascii GF file
          path: path of the ascii GF file
        """
        try:
            ifp = open(path, 'r')
        except:
            return False

        self.fileType = ''
        self.comment = []
        self.dataset = []

        # read header ("#A_GF_XX")
        try:
            line = ifp.readline()
        except:
            ifp.close()
            return False
        if not line.startswith("#A_GF_"):
            ifp.close()
            return False
        self.fileType = line.strip()

        # read size of comment list (n)
        try:
            line = ifp.readline()
        except:
            return False
        buff = line.split()
        if len(buff) < 1:
            return False
        ncl = int(buff[0])

        # read comment list ("xxx...") * ncl
        for i in range(ncl):
            try:
                line = ifp.readline()
            except:
                return False
            self.comment.append( line.rstrip() )
            continue

        # read dataset list
        dataset = GF_DATASET()
        while ( dataset.read_ascii(ifp) ):
            self.dataset = self.dataset + [dataset,]
            dataset = GF_DATASET()
            continue

        ifp.close()
        if len(self.dataset) < 1:
            return False
        return True

    def write(self, path, obo = '='):
        """
        write into a binary GF file
          path: path of the binary GF file
          obo: byte order, '<' as little-endian, '>' as big-endian,
               '=' as system byte order.
        """
        if len(self.dataset) < 1:
            return False
        if len(self.fileType) != 8:
            return False
        try:
            ofp = open(path, 'wb')
        except:
            return False

        # write header
        sz = 8
        try:
            ofp.write(struct.pack(obo+'i8si', sz, self.fileType, sz))
        except:
            ofp.close()
            return False

        # write size of comment list
        sz = 4
        try:
            ofp.write(struct.pack(obo+'iii', sz, len(self.comment), sz))
        except:
            ofp.close()
            return False

        # write comment list
        for i in range(len(self.comment)):
            try:
                ofp.write(struct.pack(obo+'i60si', sz, self.comment[i], sz))
            except:
                ofp.close()
                return False
            continue

        # write dataset list
        for i in range(len(self.dataset)):
            if not self.dataset[i].write(ofp, obo):
                ofp.close()
                return False
            continue

        # write trailer
        sz = 8
        try:
            ofp.write(struct.pack(obo+'i8si', sz, '#ENDFILE', sz))
        except:
            ofp.close()
            return False

        ofp.close()
        return True


if __name__ == '__main__':
    gf = GF_FILE()
    binary = True
    for f in sys.argv[1:]:
        if f == '-a':
            binary = False
            continue
        if f == '-b':
            binary = True
            continue

        if binary:
            ret = gf.read(f)
        else:
            ret = gf.read_ascii(f)
        if ret:
            print('file: ' + f)
            print(gf)
            for ds in gf.dataset:
                print(ds)
                for d in ds.data:
                    print(d)
        else:
            print('file: ' + f + '... read failed')
        continue
    sys.exit()
