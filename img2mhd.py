#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import os.path
import numpy
import json
import imghdr
from PIL import Image



# ================================================================================
#       Prints the help message (also done when the parameters where wrong!)
# ================================================================================
def printHelp():
    print("\nimg2mhd.py : Converting sliced image(s) and metadata to mhd (+raw) format\n"
            + "=========================================================================\n")

    print("USAGE:\n"
            + "\tpython3 img2mhd.py -type {Image Type} -series {Series} -in {Files} -meta {Files} -out {File}\n\n"
            + "Input image type:\t{jpg/jpeg | png | gif | tiff | bmp | rgb | pbm/pgm/ppm | webp}\n"
            + "Input series:\t\t{MRA | DSA}\n"
            + "Input files:\t\t{Single image file | Folder containing sorted images}\n"
            + "Meta information:\tMeta.json\n"
            + "Output file:\t\t{Output filename | Output folder}\n")



# ================================================================================
#                   Returns the image header size in bytes
# ================================================================================
def getHeaderSize(path):
    if (os.path.isfile(path)):
        ft = imghdr.what(path)

        if ft == "jpeg":
            # Header: "Magic Number" (0xffd8)
            return 2
        elif ft == "png":
            # Header: "Magic Number" (0x89504e470d0a1a0a)
            return 8
        elif ft == "gif":
            # Header: "Magic Number" (0x474946383961 / 0x474946383761)
            return 6
        elif ft == "tiff":
            # Header: "Magic Number" (0x49492a00 / 0x4d4d002a)
            return 8
        elif ft == "bmp":
            # Header: "Magic Number" (0x424d) + 3 more information fields
            return 14
        elif ft == "rgb":
            # Header: "Magic Number" (0x01da) + 12 more information fields
            return 512
        elif ft == "pbm":
            # Header: "Magic Number" (0x50310a / 0x50340a)
            return 3
        elif ft == "pgm":
            # Header: "Magic Number" (0x50320a / 0x50350a)
            return 3
        elif ft == "ppm":
            # Header: "Magic Number" (0x50330a / 0x50360a)
            return 3
        elif ft == "webp":
            # Header: "Magic Number" (0x52494646) + 4 Byte information field + (0x57454250)
            return 20
        elif ft == "exr":
            # Header: "Magic Number" (0x762f3101)
            pass
        elif ft == "rast":
            # Header: ?
            pass
        elif ft == "xbm":
            # Header: ?
            pass

    return None


# ================================================================================
#           Returns the name of the dict field searched for using regex
# ================================================================================
def getFieldName(name, data):
    out = list(filter(re.compile(
        r'(?i)%s$' % name.replace(" ", " +")
    ).match, data))

    return out[0] if len(out) == 1 else None



# ================================================================================
#               Validates that all parameters given are correct!
#   TODO: handle meta information using other file name or another format
# ================================================================================
def validateParameters(args):
    try:
        idx_type = args.index("-type")
        img_type = args[idx_type+1]
    except Exception:
        # No type given!
        return None

    del args[idx_type+1]
    del args[idx_type]

    try:
        idx_series = args.index("-series")
        img_series = args[idx_series+1]
    except Exception:
        # No series given!
        return None

    del args[idx_series+1]
    del args[idx_series]

    try:
        idx_in = args.index("-in")
        img_path = args[idx_in+1]
    except Exception:
        # No input file/ folder given
        return None

    del args[idx_in+1]
    del args[idx_in]

    try:
        idx_out = args.index("-out")
        out_path = args[idx_out+1]
    except Exception:
        # No output folder given
        return None

    del args[idx_out+1]
    del args[idx_out]

    try:
        idx_me = args.index("-meta")
        meta_json = args[idx_me+1]

        assert bool(re.search(r'(?i)meta.json', args[idx_me+1]))
    except Exception:
        # No Meta.json given (or using another name which is not implemented yet!)
        return None

    # Return everything structured
    return {
        "in_meta" : meta_json,
        "in_series": img_series,
        "in_img" :  img_path,
        "img_type" : img_type,
        "out_path" : out_path
    }


# ================================================================================
#                       Validate given Series (MRA / DSA)
# ================================================================================
def validateSeries(given):
    return given.upper() in ["DSA", "MRA"]


# ================================================================================
#               Check if Image input is a single file or folder
# ================================================================================
def validateImage(path, img_type):
    files = []
    if os.path.isdir(path):
        for file in os.listdir(path):
            # Disallow mask files
            if "mask" in file:
                continue

            # Check if file name ("type") equals given type
            if bool(re.search(img_type, file.split(".")[-1::][0], re.IGNORECASE)):
                files.append(path + file)
    elif os.path.isfile(path):
        # Check if file name ("type") equals given type
        if bool(re.search(img_type, path.split(".")[-1::][0], re.IGNORECASE)):
            files.append(path)

    return files


# ================================================================================
#                   Check if Meta.json is formatted correctly
#
#   File should include MRA field, looking sth. like this:
#   "MRA" : {
#       "rows" : Int
#       "columns" : Int
#       "number of slices" : Int => should equal number of given images!
#       "slice thickness" : Float
#       "slice spacing" : Float
#       "pixel spacing" : [Float, Float]
#   }
# ================================================================================
def validateMeta(path):
    with open(path, "r") as in_file:
        data = json.load(in_file)

    cols = rows = pxl_size = pxl_space_x = pxl_space_y = pxl_space_z = None

    # Check if there is a MRA field in JSON
    found = getFieldName("mra", data)
    if found != None:
        data = data[found]

        found = [
            getFieldName("columns", data),
            getFieldName("rows", data),
            getFieldName("slice thickness", data),
            getFieldName("pixel spacing", data),
            getFieldName("slice spacing", data)
        ]
        if not None in found:
            cols = data[found[0]]
            rows = data[found[1]]
            pxl_size = data[found[2]]
            pxl_space_x = data[found[3]][0]
            pxl_space_y = data[found[3]][1]
            pxl_space_z = data[found[4]]

    return cols, rows, pxl_size, pxl_space_x, pxl_space_y, pxl_space_z



# ================================================================================
#                                   MAIN-ROUTINE:
#   1) Validation of parameters
#   2) Validation of input file/folder
#   3) Validation of images (if folder was given)
#   4) Validation of meta data
#   5) MHD output
#   6) RAW output (if file was given)
# ================================================================================
if __name__ == "__main__":
    args = sys.argv[1::]
    if len(args) == 0:
        print("No parameters where given!")
        printHelp()
        exit(1)


    #   Validate parameters
    #   ===================
    res = validateParameters(args)
    if not res:
        # Parameters are not correct!
        print("Parameters are not correct!")
        printHelp()
        exit(2)


    #   Validate series
    #   ===============
    if not validateSeries(res["in_series"]):
        # Series is neather DSA nor MRA
        print("Wrong Series given!")
        printHelp()
        exit(3)


    #   Validate input file/ folder is correct
    #   ======================================
    files = validateImage(res["in_img"], res["img_type"])
    if len(files) == 0:
        print("No suitable path given or directory does not contain images from given type!")
        printHelp()
        exit(4)

    header_size = getHeaderSize(files[0])
    im = Image.open(files[0])
    width, height = im.size
    bit_depth = im.mode

    if len(files) != 1:
        for i in range(1, len(files)-1):
            im = Image.open(files[0])
            lwidth, lheight = im.size
            lbit_depth = im.mode

            if getHeaderSize(files[i]) != header_size \
                or width != lwidth or height != lheight or bit_depth != lbit_depth:
                print("Images differ in type or size, information does not match!")
                printHelp()
                exit(5)


    #   Validate meta data
    #   ==================
    meta_info = validateMeta(res["in_meta"])
    if None in meta_info:
        print("Meta.json was not fully functional as relevant portions for MHD where missing!")
        printHelp()
        exit(6)


    #   Create MHD file from skeleton
    #   =============================
    #   TODO: Fields: Position, Orientation, AnatomicalOrientation, ElementNumberOfChannels
    information = [
        "ObejctType = Image",
        "NDims = 3",
        "DimSize = ",
        "ElementType = ",
        "HeaderSize = ",
        "BinaryData = True ",
        "BinaryDataByteOrderMSB = ",
        "ElementSize = ",
        "ElementSpacing = ",
        "ElementByteOrderMSB = ",
        "ElementDataFile = "
    ]

    # Data type of image(s) (https://pillow.readthedocs.io/en/5.1.x/handbook/concepts.html#modes)
    if bit_depth in ['1', 'L', 'La', 'LA', 'P', 'PA', 'RGB', 'RGBX', 'RGBa', 'RGBA', 'CMYK', 'YCbCr', 'LAB', 'HSV']:
        # Everything 1 Byte data types -> MET_UCHAR or MET_CHAR (assume first)
        information[3] += "MET_UCHAR"
    elif bit_depth in ['I;16', 'I;16L', 'I;16B', 'I;16N', 'BGR;15', 'BGR;16']:
        # 2 Byte unsigned integer pixels -> MET_USHORT
        information[3] += "MET_USHORT"
    elif bit_depth in ['BGR;24', 'BGR;32']:
        # 4 Byte unsigned integer pixels -> MET_UINT
        information[3] += "MET_UINT"
    elif bit_depth == "I":
        # 4 Byte signed integer pixels -> MET_INT
        information[3] += "MET_INT"
    elif bit_depth == "F":
        # 4 Byte floating point pixels -> MET_FLOAT
        information[3] += "MET_FLOAT"
    else:
        print(f"The given image(s) bitdepth was not 8-Bit, 16-Bit, 32-Bit, 64-Bit! or it was not implemented (correctly): {bit_depth}")
        printHelp()
        exit(7)

    # HeaderSize (in Bytes, RAW have none)
    if len(files) != 1:
        information[4] += str(0) #str(int(header_size/8))
    else:
        information[4] += str(0)

    # Dimensions of output voxel box (width + length)
    information[2] += str(width) + " " + str(height)

    if res["in_series"].upper() == "DSA":
        # Dimensions of output voxel box (height)
        information[2] += " " + 1

        # ElementSize (X Y Z)
        information[7] += "1 1 1"

        # ElementSpacing (X Y Z)
        information[8] += "1 1 1"
    else:
        # Dimensions of output voxel box (height)
        information[2] += " " + str(len(files))

        # ElementSize (X Y Z)
        information[7] += str(meta_info[2]) + " " + str(meta_info[2]) + " " + str(meta_info[2])

        # ElementSpacing (X Y Z)
        information[8] += str(meta_info[3]) + " " + str(meta_info[4]) + " " + str(meta_info[5])

    # ElementByteOrderMSB
    if sys.byteorder == "little":
        information[6] += "False"
        information[9] += "False"
    else:
        information[6] += "True"
        information[9] += "True"

    # ElementDataFile (one or list)
    if len(files) != 1:
        try:
            # sort by file names where filenames are numbers only (0.xyz ... 1000.xyz ...)
            files.sort(key = lambda file: int(file.split(os.path.sep)[-1::][0].split(".")[0]))
        except Exception:
            print("MHD files require slices (images) to be sorted but given file names can not be sorted!")
            printHelp()
            exit(8)

        information[10] += "LIST 2D"
        for file in files:
            information.append(file.split(os.path.sep)[-1::][0] + ".raw")
    else:
        information[10] += files[0].split(os.path.sep)[-1::][0] + ".raw"

    # Create output folder if nonexistant
    os.makedirs(res["out_path"], exist_ok=True)

    # Output MHD skeleton to file
    with open(os.path.join(res["out_path"], "output.mhd"), "w") as mhd:
        for i in range(0, len(information)):
            mhd.write(information[i] + "\n")


    #   Create RAW image if only one image is given
    #   ===========================================
    if   "MET_CHAR" in information[3]:          dtype = numpy.int8 
    elif "MET_UCHAR" in information[3]:         dtype = numpy.uint8
    elif "MET_USHORT" in information[3]:        dtype = numpy.uint16
    elif "MET_SHORT" in information[3]:         dtype = numpy.int16
    elif "MET_UINT" in information[3]
      or "MET-ULONG" in information[3]:         dtype = numpy.uint32
    elif "MET_INT" in information[3]
      or "MET_LONG" in information[3]:          dtype = numpy.int32
    elif "MET_ULONG_LONG" in information[3]:    dtype = numpy.uint64
    elif "MET_LONG_LONG" in information[3]:     dtype = numpy.int64
    elif "MET_FLOAT" in information[3]:         dtype = numpy.single
    elif "MET_DOUBLE" in information[3]:        dtype = numpy.double

    for file in files:
        image_2d = numpy.array(Image.open(file))
        print(f"Typen - MHD: {information[3]} - Numpy: {image_2d.dtype}")

        # Save array to file (https://gist.github.com/jdumas/280952624ea4ad68e385b77cdba632c1#file-volume-py-L39)
        with open(os.path.join(res["out_path"], file.split(os.path.sep)[-1::][0] + ".raw"), "wb") as raw:
            raw.write(bytearray(image_2d.astype(dtype).flatten()))
