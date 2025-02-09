import bpy
import struct
import array
import os

from ..helpers.nikkireader import big_endian, read_uint16, read_float, read_uint32, read_vec2, read_vec3, read_vec4

class meshClass:
    def __init__(self, name, **properties):
        self.name = name
        self.properties = properties

    def get_property(self, key, default=[]):
        return self.properties.get(key, default)

    def set_property(self, key, value):
        self.properties[key] = value
        
    def append_property(self, key, value):
        self.properties[key] = self.properties[key].append(value)

class amo_reader():
    obj_group = []
    mat_group = []
    tex_group = []

    sub_offsets = []
    sub_sizes = []

    def read_block(self, file):
        block_pos = file.tell()
        block_id = read_uint32(file)
        block_count = read_uint32(file)
        block_size = read_uint32(file)
        match block_id:
            case 0x20000:
                print(f"Header Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                unk = read_uint32(file)
                for n in range(block_count):
                    self.read_block(file)
            case 0x2:
                print("Main Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                for n in range(block_count):
                    self.obj_group.append(meshClass(name=f"Mesh-{n}"))
                    self.read_block(file)
                #read_block(file)
            case 0x4:
                print("Object Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                for n in range(block_count):
                    self.read_block(file)
            case 0x5:
                print("Face Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                for n in range(block_count):
                    self.read_block(file)
            case 0x030000:
                print("Face Sub-Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                max_pos = (file.tell()+block_size)-12
                strips = []
                for n in range(block_count):
                    if file.tell() < max_pos:
                        if big_endian == True:
                            unk_val = read_uint16(file)
                            face_count = read_uint16(file)
                        else:
                            face_count = read_uint16(file)
                            unk_val = read_uint16(file)
                        vertices = []
                        for i in range(face_count):
                            if file.tell() < max_pos:
                                vertices.append(read_uint32(file))
                        strips.append(vertices)
                self.obj_group[-1].set_property('strips',strips)
            case 0x040000:
                print("Face Sub-Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                max_pos = (file.tell()+block_size)-12
                strips = []
                for n in range(block_count):
                    if file.tell() < max_pos:
                        if big_endian == True:
                            unk_val = read_uint16(file)
                            face_count = read_uint16(file)
                        else:
                            face_count = read_uint16(file)
                            unk_val = read_uint16(file)
                        vertices = []
                        for i in range(face_count):
                            vertices.append(read_uint32(file))
                        strips.append(vertices)
                self.obj_group[-1].set_property('strips2',strips)
            case 0x050000: # Unknown
                print("Material Remap Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                remaps = []
                for n in range(block_count):
                    remaps.append(read_uint32(file))
                self.obj_group[-1].set_property('mat_remaps',remaps)
            case 0x060000: # Unknown
                print("Material Index Buffer Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                mat_buffer = []
                for n in range(block_count):
                    mat_buffer.append(read_uint32(file))
                self.obj_group[-1].set_property('mat_buffer',mat_buffer)
            case 0x070000:
                print("Vertex Buffer Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                vert_buffer = []
                for n in range(block_count):
                    vert_buffer.append(read_vec3(file))
                self.obj_group[-1].set_property('vert_buffer',vert_buffer)
            case 0x080000:
                print("Vertex Normals Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                vert_normals = []
                for n in range(block_count):
                    vert_normals.append(read_vec3(file))
                self.obj_group[-1].set_property('vert_normals',vert_normals)
            case 0x0A0000:
                print("Vertex UVs Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                vert_uvs = []
                for n in range(block_count):
                    vert_uvs.append(read_vec2(file))
                self.obj_group[-1].set_property('vert_uvs',vert_uvs)
            case 0x0B0000:
                print("Vertex Colors Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                vert_cols = []
                for n in range(block_count):
                    vert_cols.append(read_vec4(file))
                self.obj_group[-1].set_property('vert_cols',vert_cols)
            case 0x0C0000:
                print("Vertex Weights Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                vert_weights = []
                for n in range(block_count):
                    pair_count = read_uint32(file)
                    weight_pair = []
                    for i in range(pair_count):
                        wt_bone = read_uint32(file)
                        wt_factor = read_float(file) # Game uses range 0.0 - 100.0
                        weight_pair.append([wt_bone, wt_factor/100])
                    vert_weights.append(weight_pair)
                self.obj_group[-1].set_property('vert_weights',vert_weights)
            case 0x9:
                print("Material Data Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                for n in range(block_count):
                    self.mat_group.append(meshClass(name=f"AMO Material {n}"))
                    self.mat_group[-1].set_property('unk1',read_uint32(file))
                    self.mat_group[-1].set_property('unk2',read_uint32(file))
                    self.mat_group[-1].set_property('unk3',read_uint32(file))
                    self.mat_group[-1].set_property('emission',read_vec4(file))
                    self.mat_group[-1].set_property('rgba1',read_vec4(file))
                    self.mat_group[-1].set_property('rgba2',read_vec4(file))
                    self.mat_group[-1].set_property('unk4',read_float(file))
                    self.mat_group[-1].set_property('unk5',read_uint32(file))
                    self.mat_group[-1].set_property('unkChunk',file.read(200))
                    self.mat_group[-1].set_property('texture',read_uint32(file))
            case 0xA:
                print("Texture Data Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                for n in range(block_count):
                    self.tex_group.append(meshClass(name=f"AMO Texture {n}"))
                    self.tex_group[-1].set_property('tex_type',read_uint32(file))
                    self.tex_group[-1].set_property('tex_count',read_uint32(file))
                    self.tex_group[-1].set_property('tex_size',read_uint32(file))
                    self.tex_group[-1].set_property('tex_id',read_uint32(file))
                    self.tex_group[-1].set_property('tex_width',read_uint32(file))
                    self.tex_group[-1].set_property('tex_height',read_uint32(file))
                    self.tex_group[-1].set_property('unkChunk',file.read(244))
            case _:
                print("Unknown Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                file.seek(block_size-12,1)
        return

    def parse_tristrip(self,tri_strip):
        faces = []
        
        for n in tri_strip:
            for i in range(len(n) -2):
                if i % 2 == 0:
                    faces.append([n[i],n[i+1],n[i+2]])
                else:
                    faces.append([n[i],n[i+2],n[i+1]])
        
        return faces

    def parse_amo(self, filepath, image_names):
        self.obj_group.clear()
        self.mat_group.clear()
        self.tex_group.clear()

        self.sub_offsets.clear()
        self.sub_sizes.clear()
        overall_name = os.path.basename(filepath)
        with open(filepath, 'rb') as file:
            amh_count = read_uint32(file)
            '''
            if amh_count >= 16777216:
                big_endian = True
                file.seek(0)
                amh_count = read_uint32(file)
            '''
            # Read offsets for amo/fmod and ahi/fskl
            for n in range(amh_count):
                self.sub_offsets.append(read_uint32(file))
                self.sub_sizes.append(file.tell()+read_uint32(file))
                
            # Assume amo is always first
            file.seek(self.sub_offsets[0])
            amo_header = read_uint32(file)
            amo_version = read_uint32(file)
            amo_size = read_uint32(file)
            
            while(file.tell() < self.sub_sizes[0]):
                self.read_block(file)
                
            mat_name_list = []
            
            # Actual Materials
            for idx, amo_mat in enumerate(self.mat_group):
                material = bpy.data.materials.new(name=f"{overall_name} Material {idx}")
                material.use_nodes = True
                material.use_backface_culling = False
                material.blend_method = 'CLIP'
                material.shadow_method = 'CLIP'
                node_tree = material.node_tree
                nodes = node_tree.nodes
                links = node_tree.links
                
                mat_name_list.append(material.name)
                
                for node in nodes:
                    nodes.remove(node)
                
                output_node = nodes.new(type='ShaderNodeOutputMaterial')
                output_node.location = (900,0)
                
                diffuse_node = nodes.new(type='ShaderNodeBsdfPrincipled')
                diffuse_node.location = (500,0)
                diffuse_node.inputs['Roughness'].default_value = 1.0
                color_emit = amo_mat.get_property('emission')
                avg_emit = (color_emit[0] + color_emit[1] + color_emit[2]) / 3
                if avg_emit > 0.6:
                    diffuse_node.inputs[27].default_value = avg_emit

                maprange_node = nodes.new(type='ShaderNodeMapRange')
                maprange_node.location = (300,-600)
                maprange_node.inputs[0].default_value = avg_emit
                maprange_node.inputs[1].default_value = 0
                maprange_node.inputs[2].default_value = 1
                maprange_node.inputs[3].default_value = -1
                maprange_node.inputs[4].default_value = 1
                
                mat_texture = self.tex_group[amo_mat.get_property('texture')].get_property('tex_id')
                texture_node = nodes.new(type='ShaderNodeTexImage')
                texture_node.location = (0,0)
                if image_names:
                    texture = bpy.data.images.get(image_names[mat_texture])
                    texture_node.image = texture
                
                vertcol_node = nodes.new(type='ShaderNodeVertexColor')
                vertcol_node.location = (0,-300)
                vertcol_node.layer_name = "ColRGBA"

                mix_node = nodes.new(type='ShaderNodeMix')
                mix_node.location = (300,0)
                mix_node.data_type = 'RGBA'
                mix_node.blend_type = 'MULTIPLY'
                mix_node.inputs['Factor'].default_value = 1.0

                rgba1_node = nodes.new(type='ShaderNodeCombineColor')
                rgba1_node.location = (0,-600)
                rgba1_node.inputs[0].default_value = amo_mat.get_property('rgba1')[0]
                rgba1_node.inputs[1].default_value = amo_mat.get_property('rgba1')[1]
                rgba1_node.inputs[2].default_value = amo_mat.get_property('rgba1')[2]

                rgba2_node = nodes.new(type='ShaderNodeCombineColor')
                rgba2_node.location = (0,-800)
                rgba2_node.inputs[0].default_value = amo_mat.get_property('rgba2')[0]
                rgba2_node.inputs[1].default_value = amo_mat.get_property('rgba2')[1]
                rgba2_node.inputs[2].default_value = amo_mat.get_property('rgba2')[2]
                
                alphamix_node = nodes.new(type='ShaderNodeMath')
                alphamix_node.location = (300,-300)
                alphamix_node.operation = 'MULTIPLY'
                
                links.new(texture_node.outputs['Color'],mix_node.inputs['A'])
                links.new(vertcol_node.outputs['Color'],mix_node.inputs['B'])
                links.new(mix_node.outputs['Result'],diffuse_node.inputs[0])
                links.new(mix_node.outputs['Result'],diffuse_node.inputs[26])
                links.new(vertcol_node.outputs['Alpha'],alphamix_node.inputs[0])
                links.new(texture_node.outputs['Alpha'],alphamix_node.inputs[1])
                links.new(alphamix_node.outputs[0],diffuse_node.inputs[4])
                links.new(maprange_node.outputs[0],diffuse_node.inputs[27])
                links.new(diffuse_node.outputs['BSDF'],output_node.inputs['Surface'])
                
                #mesh.materials.append(material)

            for amo_obj in self.obj_group:
                all_strips = amo_obj.get_property('strips') + amo_obj.get_property('strips2')
                faces = self.parse_tristrip(all_strips)
                
                mesh = bpy.data.meshes.new(amo_obj.name)
                obj = bpy.data.objects.new(f"{overall_name} {amo_obj.name}", mesh)
                col = bpy.data.collections[0]
                
                col.objects.link(obj)
                bpy.context.view_layer.objects.active = obj
                    
                mesh.from_pydata(amo_obj.get_property('vert_buffer'), [], faces)

                # Adapted from *&'s plugin
                mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
                mesh.normals_split_custom_set_from_vertices(amo_obj.get_property('vert_normals'))
                mesh.use_auto_smooth = True  
            
                # UVs
                if not mesh.uv_layers:
                    uv_layer = mesh.uv_layers.new(name="UVMap")
                else:
                    uv_layer = mesh.uv_layers.active
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        uv_layer.data[loop_idx].uv = amo_obj.get_property('vert_uvs')[vert_idx]
                
                # Vertex Colors
                if not mesh.vertex_colors:
                    vert_col = mesh.vertex_colors.new(name="ColRGBA")
                else:
                    vert_col = mesh.vertex_colors.active
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        vert_col.data[loop_idx].color = amo_obj.get_property('vert_cols')[vert_idx]
            
                # Weights Vertex Groups
                
                for idx, weightset in enumerate(amo_obj.get_property('vert_weights')):
                    for weight in weightset:
                        bone_name = f"Bone.{str(weight[0]).zfill(3)}"
                        if bone_name not in obj.vertex_groups:
                            vertexw_group = obj.vertex_groups.new(name=bone_name)
                        #print(f"{[idx]} {weight[0]} {weight[1]}")
                        vertexw_group.add([idx],weight[1],'ADD')
                
                # Tri-Strip Vertex Groups
                for idx, strip in enumerate(all_strips):
                    strip_name = f"Strip.{str(idx).zfill(3)}"
                    if strip_name not in obj.vertex_groups:
                        vertex_group = obj.vertex_groups.new(name=strip_name)
                        weight = 1/len(strip)
                        for vert in strip:
                            vertex_group.add([vert], weight, 'REPLACE')
                
                for mat_id in amo_obj.get_property('mat_remaps'):
                    mat_name = mat_name_list[mat_id]
                    mat_ref = bpy.data.materials.get(mat_name)
                    
                    if mat_name not in obj.data.materials:
                        obj.data.materials.append(mat_ref)
                
                for idx, mat_id in enumerate(amo_obj.get_property('mat_buffer')):
                    strip_name = f"Strip.{str(idx).zfill(3)}"
                    vert_group = obj.vertex_groups.get(strip_name)
                    
                    group_index = vert_group.index
                    group_verts = [v.index for v in obj.data.vertices if group_index in [g.group for g in v.groups]]
                    
                    for poly in obj.data.polygons:
                        if any(v in group_verts for v in poly.vertices):
                            poly.select = True
                            poly.material_index = mat_id
                        else:
                            poly.select = False