import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
import os

from .tex.tex_parser import parse_tex
from .amo.amo_parser import AMOReader
from .helpers.nikkireader import NikkiReader

bl_info = {
    "name": "Monster Hunter PS2 _amh Importer",
    "blender": (3, 6, 0),
    "version": (1, 0, 0),
    "category": "Import-Export",
}

class import_amh(Operator, ImportHelper):
    bl_idname = "mh_import.mh_amh"
    bl_label = "Import Monster Hunter _amh"

    filename_ext = ".bin"

    filter_glob: StringProperty(default="*_amh.bin")
    load_textures: BoolProperty(name="Load Textures", description="Attempt to load textures from a _tex file or a folder.", default=True)
    texture_path: StringProperty(name="Texture Path", description="Leave empty to attempt to load from _tex file", default="")
    big_endian: BoolProperty(name="MHG Wii Format", description="Attempt to load data in Big Endian mode.", default=False)

    def execute(self, context):
        NikkiReader.set_endian(self.big_endian)
        try:
            tex_list = []
            if self.load_textures:
                final_path = self.texture_path if self.texture_path != "" and os.path.isabs(self.texture_path) else self.filepath.replace("_amh","_tex")
                print (final_path)

                if os.path.isdir(final_path):
                    png_files = [f for f in os.listdir(final_path) if f.lower().endswith(".png")]
                    if not png_files:
                        print(f"No PNG files found in folder '{final_path}'.")
                    else:
                        for png_file in png_files:
                            image = bpy.data.images.load(os.path.join(final_path, png_file))
                            tex_list.append(image.name)
                else:
                    tex_list = parse_tex(final_path)
            amo_parser = AMOReader()
            amo_parser.parse_amo(self.filepath, tex_list)

            return { "FINISHED" }
        except Exception as ex:
            print('Error: ' + str(ex))

        return {"FINISHED"}

def register():
    register_material_properties()
    bpy.utils.register_class(MATERIAL_PT_AMHPanel)
    bpy.utils.register_class(import_amh)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)

def unregister():
    del bpy.types.Material.amh_diffuse
    del bpy.types.Material.amh_ambient
    bpy.utils.unregister_class(MATERIAL_PT_AMHPanel)
    bpy.utils.unregister_class(import_amh)
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)

def menu_import(self, context):
    self.layout.operator(import_amh.bl_idname, text="Import Monster Hunter PS2 model (_amh)")

# UI Stuff
def register_material_properties():
    bpy.types.Material.amh_diffuse = bpy.props.FloatVectorProperty(
        size=4,
        name="AMH Diffuse",
        subtype='COLOR',
        default=(1.0,1.0,1.0,1.0),
        min=0.0,
        max=1.0,
        description="AMH Diffuse Color"
    )
    
    bpy.types.Material.amh_ambient = bpy.props.FloatVectorProperty(
        size=4,
        name="AMH Ambient",
        subtype='COLOR',
        default=(1.0,1.0,1.0,1.0),
        min=0.0,
        max=1.0,
        description="AMH Ambient Color (Brightness)"
    )

class MATERIAL_PT_AMHPanel(bpy.types.Panel):
    bl_label = "AMH Panel"
    bl_idname = "MATERIAL_PT_AMHPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        layout = self.layout
        mat = context.material

        if mat:
            layout.prop(mat, 'amh_diffuse')
            layout.prop(mat, 'amh_ambient')
        else:
            layout.label(text="No material selected")

if __name__ == "__main__":
    register()
