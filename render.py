import bpy
import os
import glob


# ---------- USER CONFIG ----------
# STL_FILES = [
#     "/absolute/path/to/part01.stl",
#     "/absolute/path/to/part02.stl",
#     # ... up to 10 files
# ]
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
STL_FOLDER = os.path.join(BASE_DIR, "./stl_files_to_render/")
STL_FILES = sorted(glob.glob(os.path.join(STL_FOLDER, "*.stl")))

OUTPUT_DIR = os.path.join(BASE_DIR, "./output/")  # must exist
MAIN_OBJECT_NAME = "MainObject"                   # change to the object in your scene
RENDER_FORMAT = "PNG"                             # PNG, JPEG, etc.
RENDER_RESOLUTION = (1920, 1080)                  # width, height
# ---------------------------------

scene = bpy.context.scene

# ensure render settings
scene.render.image_settings.file_format = RENDER_FORMAT
scene.render.resolution_x, scene.render.resolution_y = RENDER_RESOLUTION
scene.render.resolution_percentage = 100

# get main object
main_obj = bpy.data.objects.get(MAIN_OBJECT_NAME)
if main_obj is None:
    raise RuntimeError(f"Object named '{MAIN_OBJECT_NAME}' not found in scene.")

def import_stl(filepath):
    # Import STL; imported object becomes selected/active
    bpy.ops.wm.stl_import(filepath=filepath)
    # after import, find newly imported objects (we assume single object imported)
    imported = [o for o in bpy.context.selected_objects if o.name != main_obj.name]
    if not imported:
        raise RuntimeError(f"Import of '{filepath}' produced no objects.")
    return imported[0]

def cleanup_obj(obj):
    # unlink and remove object and its mesh datablock if unused
    mesh = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    # remove mesh datablock if no users remain
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh, do_unlink=True)

os.makedirs(OUTPUT_DIR, exist_ok=True)

for stl in STL_FILES:
    name = os.path.splitext(os.path.basename(stl))[0]
    print("Processing:", stl)

    imported_obj = import_stl(stl)

    # Optional: match imported object's transforms to main_obj scale/rotation if needed:
    # imported_obj.rotation_euler = (0, 0, 0)
    # imported_obj.location = (0,0,0)
    # imported_obj.scale = (1,1,1)
    # bpy.context.view_layer.update()

    # copy mesh data (so each iteration is independent)
    new_mesh = imported_obj.data.copy()
    new_mesh.name = f"{main_obj.name}_mesh_{name}"

    # assign copied mesh to main object
    main_obj.data = new_mesh

    # copy materials from imported to main (clear first)
    main_obj.data.materials.clear()
    for mat in imported_obj.data.materials:
        main_obj.data.materials.append(mat)

    # set output filepath and render
    outpath = os.path.join(OUTPUT_DIR, f"{name}.png")
    scene.render.filepath = outpath
    bpy.ops.render.render(write_still=True)
    print("Saved render to:", outpath)

    # move .stl to done folder (optional)
    done_folder = os.path.join(STL_FOLDER, "done")
    os.makedirs(done_folder, exist_ok=True)
    os.rename(stl, os.path.join(done_folder, os.path.basename(stl)))

    # cleanup imported object and its original mesh (we already copied its mesh)
    cleanup_obj(imported_obj)

print("Batch render finished.")
