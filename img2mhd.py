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
    print("\nimg2mhd.py : Converting sliced image(s) and metadate to the mhd format\n"
            + "======================================================================\n")

    print("USAGE:\n"
            + "\tpython3 img2mhd.py -type {Image Type} -in {Files} -meta {Files} -out {File}\n\n"
            + "Input image type:\t{jpg/jpeg | png | gif | tiff | rgb | pbm/pgm | rast | xbm | bmp}\n"
            + "Input files:\t\t{Single image file | Folder containing sorted images}\n"
            + "Meta information:\tMeta.json\n"
            + "Output file:\t\t{Output filename | Output folder}\n")



# ================================================================================
#                   Returns the image header size in bytes
#           TODO: append information for other types from imghdr.py!
# ================================================================================
def getHeaderSize(path):
    if (os.path.isfile(path)):
        ft = imghdr.what(path)
        
        if ft == "jpeg":
            # Header: 0xffd8
            return 2
        elif ft == "png":
            # Header: 0x89504e470d0a1a0a
            return 8
        elif ft == "gif":
            # Header: "GIF89a" (0x474946383961)/ "GIF87a" (0x474946383761)
            return 6
        elif ft == "tiff":
            # Header:
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
            # Header: 0x50320a / 0x50350a
            return 3
        elif ft == "xbm":
            # Header: ?
            pass
        elif ft == "rast":
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

        assert bool(re.search(r'(?i)meta.json', args[idx_me+1]))
        meta_json = args[idx_me+1]
    except Exception:
        # No Meta.json given (or using another name)
        return None
    
    # Return everything structured
    return {
        "in_meta" : meta_json,
        "in_img" :  img_path,
        "img_type" : img_type,
        "out_path" : out_path
    }


# ================================================================================
#               Check if Image input is a single file or folder
# ================================================================================
def validateImage(path, img_type):
    files = []
    if os.path.isdir(path):
        for file in os.listdir(path):
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
#
#   TODO: give option to set output file name!
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
    

    #   Validate input file/ folder is correct
    #   ======================================
    files = validateImage(res["in_img"], res["img_type"])
    if len(files) == 0:
        print("No suitable path given or directory does not contain images from given type!")
        printHelp()
        exit(3)
    
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
                exit(4)
    

    #   Validate meta data
    #   ==================
    meta_info = validateMeta(res["in_meta"])
    if None in meta_info:
        print("Meta.json was not fully functional as relevant portions for MHD where missing!")
        printHelp()
        exit(5)


    #   Create MHD file from skeleton
    #   =============================
    #   TODO: handle color depth of images better
    #   TODO: change multiple images to RAW
    #   TODO: maybe create a folder with results at given output folder (xyz.out/)
    information = [
        "ObejctType = Image",
        "NDims = 3",
        "DimSize = ",
        "ElementType = ",
        "HeaderSize = -",
        "ElementSize = ",
        "ElementSpacing = ",
        "ElementByteOrderMSB = ",
        "ElementDataFile = "
    ]

    # Dimensions of output voxel box
    information[2] += str(width) + " " + str(height) + " " + str(len(files))
    
    # Data type of image(s) (https://pillow.readthedocs.io/en/5.1.x/handbook/concepts.html#modes)
    if bit_depth in ['1', 'L', 'P', 'RGB', 'RGBA', 'CMYK', 'YCbCr', 'LAB', 'HSV']:
        # Everything 1 Byte data types -> MET_UCHAR or MET_CHAR (assume first)
        information[3] += "MET_UCHAR"
    elif bit_depth == "I":
        # 4 Byte signed integer pixels -> MET_INT
        information[3] += "MET_INT"
    elif bit_depth == "F":
        # 4 Byte floating point pixels -> MET_FLOAT
        information[3] += "MET_FLOAT"
    else:
        print("The given image(s) bitdepth was not 8-Bit, 16-Bit, 32-Bit nor 64-Bit!")
        printHelp()
        exit(6)
    
    # HeaderSize (in Bytes, RAW have none)
    if len(files) != 1:
        information[4] += str(int(header_size/8))
    else:
        information[4] += str(0)

    # ElementSize (X Y Z)
    information[5] += str(meta_info[2]) + " " + str(meta_info[2]) + " " + str(meta_info[2])

    # ElementSpacing (X Y Z)
    information[6] += str(meta_info[3]) + " " + str(meta_info[4]) + " " + str(meta_info[5])

    # ElementByteOrderMSB
    if sys.byteorder == "little":
        information[7] += "False"
    else:
        information[7] += "True"

    # ElementDataFile (one or list)
    if len(files) != 1:
        try:
            # sort by file names where filenames are numbers only (0.xyz ... 1000.xyz ...)
            files.sort(key = lambda file: int(file.split("/")[-1::][0].split(".")[0]))
        except Exception:
            print("MHD files require slices (images) to be sorted but given file names can not be sorted!")
            printHelp()
            exit(7)

        information[8] += "LIST"
        for file in files:
            information.append(file)
    else:
        raw_filename = "output.raw"
        information[8] += raw_filename
    
    # Output MHD skeleton to file
    filename = "output.mhd"
    with open(filename, "w+") as mhd:
        for i in range(0, len(information)):
            mhd.write(information[i] + "\n")


    #   Create RAW image if only one image is given
    #   ===========================================
    #   TODO: look for more possible file types
    if "raw_filename" in locals():
        if "MET_UCHAR" in information[3]:
            dtype = numpy.uint8
        elif "MET_INT" in information[3]:
            dtype = numpy.uint16
        elif "MET_FLOAT" in information[3]:
            dtype = numpy.single
        
        # Rad image to array
        image_2d = numpy.array(Image.open(files[0]))

        # Save array to file (https://gist.github.com/jdumas/280952624ea4ad68e385b77cdba632c1#file-volume-py-L39)
        with open(raw_filename, "wb") as raw:
            raw.write(bytearray(image_2d.astype(dtype).flatten()))