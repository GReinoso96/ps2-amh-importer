import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
import os

from .tex.tex_parser import parse_tex
from .amo.amo_parser import amo_reader

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

    def execute(self, context):
        try:
            tex_list = []
            if self.load_textures == True:
                folder = (os.path.dirname(self.filepath))

                if self.texture_path != "":
                    folder_path = f"{folder}/{self.texture_path}"
                    
                    if os.path.isdir(folder_path):
                        if os.path.isabs(self.texture_path):
                            final_path = self.texture_path
                        else:
                            final_path = folder_path

                        png_files = [f for f in os.listdir(final_path) if f.lower().endswith(".png")]
                        if not png_files:
                            print(f"No PNG files found in folder '{final_path}'.")
                        else:
                            for png_file in png_files:
                                image_path = os.path.join(final_path, png_file)
                                
                                # Load the image into Blender
                                image = bpy.data.images.load(image_path)
                                tex_list.append(image.name)
                    else:
                        if os.path.isabs(self.texture_path):
                            final_path = self.texture_path
                        else:
                            final_path = folder_path
                        
                        tex_list = parse_tex(final_path)
                else:
                    final_path = (self.filepath).replace("amh","tex")
                    tex_list = parse_tex(final_path)
            print(tex_list)
            amo_parser = amo_reader()
            amo_parser.parse_amo(self.filepath, tex_list)

            return { "FINISHED" }
        except Exception as ex:
            print('Error: ' + str(ex))

        return {"FINISHED"}

def register():
    bpy.utils.register_class(import_amh)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)

def unregister():
    bpy.utils.unregister_class(import_amh)
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)

def menu_import(self, context):
    self.layout.operator(import_amh.bl_idname, text="Import Monster Hunter PS2 model (_amh)")

if __name__ == "__main__":
    register()
