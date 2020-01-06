# elastix-scripts-etc
Scripts etc. for working on "Rigid 2D/3D-registration of medical data using elastix" (Work)

---

## img2mhd.py
Creates a MetaIO (MHD) file from given image and meta data (and RAW image files) for use with elastix.
Supports multiple image input formats but no other formats for meta data other than JSON yet.


### TODO:
More (not yet implemented) information fields in MHD file.
- TransformMatrix (Elements as list)
- Default: TransformMatrix = 1 0 0 0 1 0 0 0 1
- CenterOfRotation (X Y Z)
- Default: CenterOfRotation = 0 0 0
- Offset (X Y Z)
- Default: Offset = 0 0 0

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
        "offset" : [
            "Float (X) (optional)",
            "Float (Y) (optional)",
            "Float (Z) (optional)"
        ],
        "center of rotation" : [
            "Float (X) (optional)",
            "Float (Y) (optional)",
            "Float (Z) (optional)"
        ],
        "transform matrix" : [
            "Float (X1) (optional)",
            "Float (X2) (optional)",
            "Float (X3) (optional)",
            "Float (Y1) (optional)",
            "Float (Y2) (optional)",
            "Float (Y3) (optional)",
            "Float (Z1) (optional)",
            "Float (Z2) (optional)",
            "Float (Z3) (optional)"
        ],
        "anatomical orientation" : "String (optional)"
        [...]
    },

    [...]
}
```
