# elastix-scripts-etc
Scripts etc. for working on "Rigid 2D/3D-registration of medical data using elastix" (Work)

---

## img2mhd.py
Creates a MetaIO (MHD) file from given image and meta data (and RAW image files) for use with elastix.
Supports multiple input formats but no other formats for meta data other than JSON yet.
Meta information (mainly fields) is case insensitive, so less error prone!


### TODO:
More (not yet implemented) information fields in MHD file.
- CompressedData (True / False)
- AnatomicalOrientation ([R|L] + [A|P] + [S|I])
- TransformMatrix (Elements as list)
- CenterOfRotation (X Y Z)
- Offset (X Y Z)
- Slicer preview is a bit overexposed! Maybe change it somehow?

Additional tags: [ITK/ MetaIO documentation](https://itk.org/Wiki/ITK/MetaIO/Documentation#Reference:_Tags_of_MetaImage)

Maybe change **Meta.json** to sth. more convenient:
```json
{
    [...],

    "MRA" : {
        "number of slices" : "Int",
        "columns" : "Int",
        "rows" : "Int",
        "pixel spacing" : [
            "Float (X)",
            "Float (Y)",
            "Float (Z)"
        ],
        "pixel thickness" : [
            "Float (X)",
            "Float (Y)",
            "Float (Z)"
        ],
        [...]
    },

    [...]
}
```
