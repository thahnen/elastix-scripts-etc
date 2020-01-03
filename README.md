# elastix-scripts-etc
Scripts etc. for working on "Rigid 2D/3D-registration of medical data using elastix" (Work)

---

## img2mhd.py
Creates a MetaIO (MHD) file from given image and meta data (and RAW image files) for use with elastix.
Supports multiple input formats but no other formats for meta data other than JSON yet.
Output can be a single RAW file (does not fully work yet) or multiple.


### TODO:
More (not yet implemented) information fields in MHD file.
- CompressedData (True / False)
- TransformMatrix (Elements as list)
- CenterOfRotation (X Y Z)
- Offset (X Y Z)

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
        "anatomical orientation" : "String"
        [...]
    },

    [...]
}
```
