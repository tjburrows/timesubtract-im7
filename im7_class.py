# Class for reading and writing IM7 files
# Stripped down version of Alan Fleming's IM module https://bitbucket.org/fleming79/im/

import ReadIM
import sys
import os
import numpy as np
from re import findall


def map_D(D, a, b, dtype):
    """Generic mapping from coordinates to pixel position
    using slope a intersect b
    returns (D - b)/a
    """
    return np.round((D - b) / a).astype(dtype)


def map_d(d, a, b, dtype):
    """Generic mapping from pixel position to coordinates
    using slope a intersect b
    returns d * a + b
    """
    return np.array(d * a + b, dtype=dtype)


def get_num(line):
    listOfNumbers = findall("[0123456789.-]+", line)
    return list(map(float, listOfNumbers))


class IM7:
    def __init__(self, loadfile):
        self.loadfile = loadfile
        self.data = {"attributes": {}, "I": None}

        self.readIM7()
        self.dtype = self.data["I"].data.dtype

    def _get_Buffer_(self):
        """
        Get buffer from self.loadfile. Only valid
        for IM7 and VC7 filetypes.
        Returns
        -------
        buff: BufferType
        """
        return ReadIM.get_Buffer_andAttributeList(self.loadfile, atts=None)[0]

    def _get_Buffer_andAttributeList(self):
        """
        Get buffer and Attribute list from self.loadfile. Only valid
        for IM7 and VC7 filetypes.
        Returns
        -------
        buff: BufferType
        atts: Attribute List
        """
        try:
            return ReadIM.get_Buffer_andAttributeList(self.loadfile)
        except IOError:
            raise IOError(
                "Problem loading file: {0}.Message: {1}".format(self.loadfile, sys.exc_info()[1])
            )

    def map_i(self, i):
        """ Map stored intensities to real intensities """
        iScale = get_num(self.data["attributes"]["_SCALE_I"])
        if not (iScale[0] == 1.0 and iScale[1] == 0.0):
            return map_d(i, iScale[0], iScale[1], self.dtype)
        else:
            return i

    def map_I(self, I):
        """Map real intensities to stored  intensities
        buffer.scaleI.factor should be set
        """
        factor = self.data["buffer"]["scaleI"]["factor"]
        offset = self.data["buffer"]["scaleI"]["offset"]
        if not (factor == 1.0 and offset == 0.0):
            return map_D(I, factor, offset, self.dtype)
        else:
            return np.array(I, dtype=self.dtype)

    def _set_buffer(self, buff):
        buff = ReadIM.BufferTypeAlt(buff, False, immutable=True)
        self.data["buffer"] = {}
        ReadIM.extra.obj2dict(buff, self.data["buffer"])

    def readIM7(self):
        """ Load the image from the the buffer/file (for .IM7 files) """

        extn = os.path.splitext(self.loadfile)[1]
        if not extn.lower() == ".im7":
            return

        try:
            buff, atts = self._get_Buffer_andAttributeList()
            attdict = ReadIM.extra.att2dict(atts)
            self.data["attributes"].update(attdict)
            vbuff, buff = ReadIM.extra.buffer_as_array(buff)
            if buff.image_sub_type > 0:
                raise TypeError("buffer does not contain an image: type = %s" % buff.image_sub_type)
            self._set_buffer(buff)
            vbuff2 = self.map_i(vbuff)
            self.data["I"] = np.ma.masked_equal(vbuff2, 0.0)

        finally:
            env = dir()
            if "vbuff" in env:
                del vbuff  # Yes you need to do this to stop memory leaks
            if "vbuff2" in env:
                del vbuff2
            if "buff" in env:
                ReadIM.DestroyBuffer(buff)
                del buff
            if "atts" in env:
                ReadIM.DestroyAttributeListSafe(atts)
                del atts
            if "attdict" in env:
                del attdict

    def update_attributes_with_scales(self):
        """ update self.attributes with scaling information """
        # transfer buffer info from v. Useful for writing files.

        # purge the frame scales # probably develop a better way to handle this.
        for p in [att for att in self.data["attributes"] if att.find("FrameScale") == 0]:
            self.data["attributes"].pop(p)

        for p in [att for att in self.data["attributes"] if att.find("_SCALE_") == 0]:
            self.data["attributes"].pop(p)

        for a in self.data["buffer"]:
            if a.find("scale") == 0:
                sc = self.data["buffer"][a]

                # parse the info from the buffer in suitable format

                # only work for frame0 at present

                _key = "_SCALE_%s" % a[-1].upper()
                _val = "{0:0.6f} {1:0.6f}\n{2}\n\n".format(
                    sc["factor"], sc["offset"], sc["unit"].strip("\n").strip("\x00")
                )
                self.data["attributes"][_key] = _val

                val = "{0:0.6g}\n{1:0.6g}\n{2}\n".format(
                    sc["factor"], sc["offset"], sc["unit"].strip("\n").strip("\x00")
                )
                key = "FrameScale%s0" % a[-1].upper()
                self.data["attributes"][key] = val

    def _im7_writer(self, dst):
        """ write the current buffer as masked to dst """

        buff = ReadIM.BufferTypeAlt(self.data["buffer"])
        buff.isFloat = self.dtype == np.float32

        try:
            # DaVis objects
            buff, error_code = ReadIM.extra.createBuffer(buff)

            if error_code > 1:
                raise IOError("Error code %s=%s" % (ReadIM.ERROR_CODES[error_code], error_code))

            vbuff, buff2 = ReadIM.extra.buffer_as_array(buff)

            self.update_attributes_with_scales()
            atts = ReadIM.load_AttributeList(self.data["attributes"])

            vbuff[:] = 0
            setzero = np.logical_not(self.data["I"].mask)

            vbuff[:] = self.map_I(self.data["I"]) * setzero

            # write from buffer
            err = ReadIM.WriteIM7(dst, True, buff2, atts.next)

            if err:
                codes = codes = dict(
                    [
                        (getattr(ReadIM.core, f), f)
                        for f in dir(ReadIM.core)
                        if f.find("IMREAD_ERR") == 0
                    ]
                )
                if err == 1:
                    print(
                        "Note that you cannot write into the top level directory for some strange reason"
                    )
                raise IOError("Error writing file: %s=%s" % (err, codes[err]))

            print("Created %s" % os.path.basename(dst))

        # clean up
        finally:
            env = dir()
            if "vbuff " in env:
                del vbuff  # Yes you need to do this to stop memory leaks
            if "buff" in env:
                ReadIM.DestroyBuffer(buff)
                del buff
            if "buff2" in env:
                ReadIM.DestroyBuffer(buff2)
                del buff2
            if "atts" in env:
                ReadIM.DestroyAttributeListSafe(atts)
                del atts

    def writeIM7(self, dst):
        """write the data to a .im7 file
        if frame is None dst assumes that dst is a directory
        else
        """
        ext = ".im7"
        if not ext == dst[-4:].lower():
            dst += ext
        dst = os.path.abspath(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        self._im7_writer(dst)
        return dst
