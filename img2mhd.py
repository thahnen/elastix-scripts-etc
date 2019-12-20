#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import os
import os.path
import numpy
import json
import imghdr
from PIL import Image



# ================================================================================
#       Prints the help message (also done when the parameters where wrong!)
# ================================================================================
def printHelp(topic = None):
    if topic == "type":
        print("Type")
    elif topic == "series":
        print("Series")
    elif topic == "input":
        print("Input file/ folder")
    elif topic == "meta":
        print("Meta file")
    elif topic == "output":
        print("Output folder")
    elif topic == "raw":
        print("RAW output file(s)")
    else:
        print("\nimg2mhd.py : Converting sliced image(s) and metadata to mhd (+raw) format\n"
                + "=========================================================================\n")

        print("USAGE:\n"
                + "\tpython3 img2mhd.py -type {Image type} -series {Series} -in {Files} -meta {Files} -out {File} -raw {Type}\n\n\n"
                + "Image type:\t\t{JPG/JPEG | BMP/DIB | XBM/XPM | PPM/PBM/PGM/PNM | PNG | EPS | IM | TGA | WEBP | FPX | PCD | PIXAR | PSD}\n"
                + "\t\t\t=> Default: PNG\n\n"
                + "Input series:\t\t{MRA | DSA}\n"
                + "\t\t\t=> Default: MRA\n\n"
                + "Input files:\t\t{Single image | Folder containing SORTED images}\n\n"
                + "Meta information:\tMeta.json\n\n"
                + "Output files:\t\t{Output filename | Output folder}\n"
                + "\t\t\t=> Default: Current Directory\n\n"
                + "Output RAW iamges:\t{Simple | Multiple}\n"
                + "\t\t\t=> Default: Simple\n\n"
                + "For more information on different parameters use:\n"
                + "\tpython3 img2mhd.py -h {type | series | in | meta | out | raw}\n")


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
#   TODO: handle parameters correctly (assert that "-type -series" is not valid)
# ================================================================================
def validateParameters(args):
    try:
        index = args.index("-type")
        img_type = args[index+1]
        
        del args[index+1]
        del args[index]
    except Exception:
        # No type given - assert PNG
        img_type = "PNG"

    try:
        index = args.index("-series")
        img_series = args[index+1]

        del args[index+1]
        del args[index]
    except Exception:
        # No series given - assert MRA
        img_series = "MRA"
    
    try:
        index = args.index("-raw")
        out_raw = args[index+1]

        del args[index+1]
        del args[index]
    except Exception:
        # No info on raw output given - assert SIMPLE
        out_raw = "SIMPLE"

    try:
        index = args.index("-out")
        out_path = args[index+1]

        del args[index+1]
        del args[index]
    except Exception:
        # No output folder given - assert CWD
        out_path = os.getcwd()

    try:
        index = args.index("-in")
        img_path = args[index+1]
    except Exception:
        # No input file/ folder given
        return None

    del args[index+1]
    del args[index]

    try:
        index = args.index("-meta")
        meta_json = args[index+1]

        assert bool(re.search(r'(?i)meta.json', args[index+1]))
    except Exception:
        # No Meta.json given (or using another name which is not implemented yet!)
        return None

    # Return everything structured
    return {
        "in_meta" : meta_json,
        "in_series": img_series,
        "in_img" :  img_path,
        "img_type" : img_type,
        "out_path" : out_path,
        "out_raw" : out_raw
    }


# ================================================================================
#                               Validate image type
# ================================================================================
def validateImageType(given):
    given = given.upper()

    # Supported types
    if given in [
            "BMP", "DIB",                   # BMP format
            "XBM", "XPM",                   # X BitMap format
            "JPG", "JPEG",                  # JPEG format
            "PPM", "PBM", "PGM", "PNM",     # Netpbm format
            "PNG", "EPS", "IM", "TGA", "WEBP" "FPX", "PCD", "PIXAR", "PSD"]:
        return True

    # Not yet supported types
    if given in [
            "FLIC", "FLI", "FLC",           # Flic Animation format
            "TIFF",                         # Tagged Image File Format (one or multiple)
            "GIF"]:                         # Graphics Interchange Format
        print(f"\nThe given format {given} is not yet supported! May come in the future!\n")

    return False


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
                 files.append(os.path.join(path, file))
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
#
#   TODO: append test for anatomical orientation and add default values!
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
#   1) Validate parameters
#   2) Validate input image type
#   3) Validate series type
#   4) Validate input file/folder
#   5) Validate meta information
#   6) Validate output folder
#   7) Validate RAW output type
#   8) MHD output
#   9) RAW output
# ================================================================================
if __name__ == "__main__":
    args = sys.argv[1::]
    if len(args) == 0:
        print("No parameters where given!")
        printHelp()
        exit(1)


    #   Check for help request
    #   ======================
    #   TODO: implement help
    if args[0] == "-h":
        print("Help was called!")
        exit()


    #   Validate parameters
    #   ===================
    res = validateParameters(args)
    if not res:
        # Parameters are not correct!
        print("Parameters are not correct!")
        printHelp()
        exit(2)

    #   Validate input image type
    #   =========================
    if not validateImageType(res["img_type"]):
        # Image type not supported
        print("Image type is not supported (yet)!")
        printHelp()
        exit(3)


    #   Validate series type
    #   ====================
    if not validateSeries(res["in_series"]):
        # Series is neather DSA nor MRA
        print("Wrong Series given!")
        printHelp()
        exit(4)

    
    #   Validate RAW output
    #   ===================
    #   TODO: implement validation function!


    #   Validate input file/ folder is correct
    #   ======================================
    files = validateImage(res["in_img"], res["img_type"])
    if len(files) == 0:
        print("No suitable path given or directory does not contain images from given type!")
        printHelp()
        exit(5)

    im = Image.open(files[0])
    width, height = im.size
    bit_depth = im.mode

    if len(files) != 1:
        for i in range(1, len(files)-1):
            im = Image.open(files[0])
            lwidth, lheight = im.size
            lbit_depth = im.mode

            if width != lwidth or height != lheight or bit_depth != lbit_depth:
                print("Images differ in type or size, information does not match!")
                printHelp()
                exit(6)


    #   Validate meta data
    #   ==================
    meta_info = validateMeta(res["in_meta"])
    if None in meta_info:
        print("Meta.json was not fully functional as relevant portions for MHD where missing!")
        printHelp()
        exit(7)


    #   Create MHD file from skeleton
    #   =============================
    #   TODO: Fields: Position, Orientation, AnatomicalOrientation, ElementNumberOfChannels
    information = [
        "ObejctType = Image",
        "NDims = 3",
        "DimSize = ",
        "ElementType = ",
        "HeaderSize = 0",
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
        print(f"The given image(s) bitdepth was not 8-Bit, 16-Bit, 32-Bit, 64-Bit or it was not implemented (correctly): {bit_depth}")
        printHelp()
        exit(8)

    # Dimensions of output voxel box (width + length)
    information[2] += str(width) + " " + str(height)

    if res["in_series"].upper() == "DSA":
        # Dimensions of output voxel box (height)
        information[2] += " " + str(len(files))

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
    # TODO: change single output file name
    if len(files) != 1 and res["out_raw"] != "Simple":
        try:
            # sort by file names where filenames are numbered ([…].0.xyz ... […].1000.xyz ...)
            files.sort(key = lambda file: int(file.split(os.path.sep)[-1::][0].split(".")[-2]))
        except Exception:
            print("MHD files require slices (images) to be sorted but given file names can not be sorted!")
            printHelp()
            exit(9)

        information[10] += "LIST 2D"
        for file in files:
            # replace the file extension with raw
            information.append(
                os.path.splitext(file.split(os.path.sep)[-1::][0])[0] + ".raw"
            )
    else:
        information[10] += "output.raw"

    # Create output folder if nonexistant
    os.makedirs(res["out_path"], exist_ok=True)

    # Output MHD skeleton to file
    with open(os.path.join(res["out_path"], "output.mhd"), "w") as mhd:
        for i in range(0, len(information)):
            mhd.write(information[i] + "\n")


    #   Create RAW image if only one image is given
    #   ===========================================
    #   TODO: change "image" names to raw, remove png
    if    "MET_CHAR" in information[3]:          dtype = numpy.int8 
    elif  "MET_UCHAR" in information[3]:         dtype = numpy.uint8
    elif  "MET_USHORT" in information[3]:        dtype = numpy.uint16
    elif  "MET_SHORT" in information[3]:         dtype = numpy.int16
    elif ("MET_UINT" in information[3] or
          "MET-ULONG" in information[3]):        dtype = numpy.uint32
    elif ("MET_INT" in information[3] or
          "MET_LONG" in information[3]):         dtype = numpy.int32
    elif  "MET_ULONG_LONG" in information[3]:    dtype = numpy.uint64
    elif  "MET_LONG_LONG" in information[3]:     dtype = numpy.int64
    elif  "MET_FLOAT" in information[3]:         dtype = numpy.single
    elif  "MET_DOUBLE" in information[3]:        dtype = numpy.double


    if res["out_raw"] == "Simple":
        images = numpy.array(Image.open(files[0]))
        if len(files) > 1:
            for i in range(1, len(files)):
                image_2d = numpy.array(Image.open(files[i]))
                images = numpy.append(images, image_2d)
        with open(os.path.join(res["out_path"], "output.raw"), "wb") as raw:
            raw.write(bytearray(images.astype(dtype).flatten()))
    else:
        for file in files:
            image_2d = numpy.array(Image.open(file))

            # Save array to file (https://gist.github.com/jdumas/280952624ea4ad68e385b77cdba632c1#file-volume-py-L39)
            with open(os.path.join(res["out_path"], file.split(os.path.sep)[-1::][0] + ".raw"), "wb") as raw:
                raw.write(bytearray(image_2d.astype(dtype).flatten()))
