import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
import os, sys

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
    ignore_emissive: BoolProperty(name="Ignore Emissive", description="Ignore the emissive value, tick this for stages.", default=False)
    ignore_additive: BoolProperty(name="Ignore Additive Alpha", description="Do not handle additive alpha materials.", default=False)
    rotate_delta: BoolProperty(name="Delta Rotation", description="Rotate model for Z-up.", default=True)

    def __init__(self):
        self.file_meta = []

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
            
            with open(self.filepath, 'rb') as file:
                file_count = NikkiReader.read_uint32(file)

                for n in range(file_count):
                    # Offset and Size
                    ptr = NikkiReader.read_uint32(file)
                    size = NikkiReader.read_uint32(file)
                    self.file_meta.append([ptr,size])
                
                subfile = NikkiReader.create_subfile(file, self.file_meta[0][0], self.file_meta[0][1])
                amo_parser = AMOReader(tex_list)
                amo_parser.rotate_delta = self.rotate_delta
                amo_parser.ignore_additive = self.ignore_additive
                amo_parser.ignore_emissive = self.ignore_emissive
                amo_parser.load_amo(subfile, os.path.basename(self.filepath))

            return { "FINISHED" }
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno, str(ex))

        return {"FINISHED"}

class import_amo(Operator, ImportHelper):
    bl_idname = "mh_import.mh_amo"
    bl_label = "Import Monster Hunter AMO (fmod)"

    filename_ext = ".fmod"

    filter_glob: StringProperty(default="*.fmod", options={'HIDDEN'})
    load_textures: BoolProperty(name="Load Textures", description="Attempt to load textures from a _tex file or a folder.", default=False)
    texture_path: StringProperty(name="Texture Path", description="Leave empty to attempt to load from _tex file", default="")
    ignore_emissive: BoolProperty(name="Ignore Emissive", description="Ignore the emissive value, tick this for stages.", default=False)
    ignore_additive: BoolProperty(name="Ignore Additive Alpha", description="Do not handle additive alpha materials.", default=False)
    rotate_delta: BoolProperty(name="Delta Rotation", description="Rotate model for Z-up.", default=True)

    file_meta = []

    def execute(self, context):
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
            
            with open(self.filepath, 'rb') as file:
                amo_parser = AMOReader(tex_list)
                amo_parser.rotate_delta = self.rotate_delta
                amo_parser.ignore_additive = self.ignore_additive
                amo_parser.ignore_emissive = self.ignore_emissive
                amo_parser.load_amo(file, os.path.basename(self.filepath))

            return { "FINISHED" }
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno, str(ex))

        return {"FINISHED"}

def register():
    register_material_properties()
    bpy.utils.register_class(MATERIAL_PT_AMHPanel)
    bpy.utils.register_class(import_amh)
    bpy.utils.register_class(import_amo)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)

def unregister():
    del bpy.types.Material.amh_diffuse
    del bpy.types.Material.amh_ambient
    bpy.utils.unregister_class(MATERIAL_PT_AMHPanel)
    bpy.utils.unregister_class(import_amh)
    bpy.utils.unregister_class(import_amo)
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)

def menu_import(self, context):
    self.layout.operator(import_amh.bl_idname, text="Import Monster Hunter model (_amh)")
    self.layout.operator(import_amo.bl_idname, text="Import Monster Hunter model (fmod)")

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
