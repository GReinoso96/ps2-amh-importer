import bpy, bmesh
import math

from ..helpers.nikkireader import NikkiReader

class MeshClass:
    def __init__(self, name: str, **properties):
        self.name = name
        self.properties = properties
    
    def get_property(self, key, default=None):
        return self.properties.get(key, default if default is not None else [])
    
    def set_property(self, key, value):
        self.properties[key] = value

    def append_property(self, key, value):
        if key not in self.properties:
            self.properties[key] = []
        self.properties[key].append(value)

class AMOReader:
    def __init__(self, img_names):
        self.obj_group = []
        self.mat_group = []
        self.tex_group = []
        self.sub_offsets = []
        self.sub_sizes = []
        self.image_names = img_names
        self.ignore_emissive = False
        self.ignore_additive = False
        self.rotate_delta = True
    
    def read_block(self, file):
        block_pos = file.tell()
        block_id = NikkiReader.read_uint32(file)
        block_count = NikkiReader.read_uint32(file)
        block_size = NikkiReader.read_uint32(file)

        block_names = {
            0x20000: 'Header',
            0x2: 'Main',
            0x4: 'Object',
            0x5: 'Face',
            0x030000: 'Face Sub1',
            0x040000: 'Face Sub2',
            0x050000: 'Material Remap',
            0x060000: 'Material Index',
            0x070000: 'Vertex Buffer',
            0x080000: 'Vertex Normals',
            0x0A0000: 'Vertex UVs',
            0x0B0000: 'Vertex Colors',
            0x0C0000: 'Vertex Weights',
            0x0F0000: 'Render Flag',
            0x9: 'Materials',
            0xA: 'Textures'
        }

        print(f"{block_names.get(block_id, 'Unknown').rjust(16)} | {block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")

        block_handlers = {
            0x20000: self.handle_header_block,
            0x2: self.handle_main_block,
            0x4: self.handle_object_block,
            0x5: self.handle_face_block,
            0x030000: self.handle_face_sub_block,
            0x040000: self.handle_face_sub_block2,
            0x050000: self.handle_material_remap_block,
            0x060000: self.handle_material_index_block,
            0x070000: self.handle_vertex_buffer_block,
            0x080000: self.handle_vertex_normals_block,
            0x0A0000: self.handle_vertex_uvs_block,
            0x0B0000: self.handle_vertex_colors_block,
            0x0C0000: self.handle_vertex_weights_block,
            0x0F0000: self.handle_renderflag_block,
            0x9: self.handle_material_data_block,
            0xA: self.handle_texture_data_block
        }

        handler = block_handlers.get(block_id, self.handle_unknown_block)
        handler(file, block_count, block_size)
    
    def handle_header_block(self, file, count, size):
        NikkiReader.read_uint32(file) # Unknown Numbers
        for _ in range(count):
            self.read_block(file)
    
    def handle_main_block(self, file, count, size):
        for n in range(count):
            self.obj_group.append(MeshClass(name=f"Mesh-{n}"))
            self.read_block(file)
    
    def handle_object_block(self, file, count, size):
        for _ in range(count):
            self.read_block(file)
    
    def handle_face_block(self, file, count, size):
        for _ in range(count):
            self.read_block(file)
    
    def handle_face_sub_block(self, file, count, size):
        self._parse_face_sub_block(file, count, size, 'strips')
    
    def handle_face_sub_block2(self, file, count, size):
        self._parse_face_sub_block(file, count, size, 'strips2')
    
    def _parse_face_sub_block(self, file, count, size, property_name):
        max_pos = (file.tell() + size) - 12
        strips = []
        for _ in range(count):
            if file.tell() < max_pos:
                val1 = NikkiReader.read_uint16(file)
                val2 = NikkiReader.read_uint16(file)
                face_count = val2 if NikkiReader._big_endian else val1
                vertices = [NikkiReader.read_uint32(file) for _ in range(face_count) if file.tell() < max_pos]
                strips.append(vertices)
        
        self.obj_group[-1].set_property(property_name, strips)
    
    def handle_material_remap_block(self, file, count, size):
        self.obj_group[-1].set_property('mat_remaps', [NikkiReader.read_uint32(file) for _ in range(count)])
    
    def handle_material_index_block(self, file, count, size):
        self.obj_group[-1].set_property('mat_buffer', [NikkiReader.read_uint32(file) for _ in range(count)])
    
    def handle_vertex_buffer_block(self, file, count, size):
        self.obj_group[-1].set_property('vert_buffer', [NikkiReader.read_vec3(file) for _ in range(count)])
    
    def handle_vertex_normals_block(self, file, count, size):
        self.obj_group[-1].set_property('vert_normals', [NikkiReader.read_vec3(file) for _ in range(count)])
    
    def handle_vertex_uvs_block(self, file, count, size):
        vert_uvs = []
        for _ in range(count):
            x = NikkiReader.read_float(file)
            y = NikkiReader.read_float(file) * -1
            vert_uvs.append([x,y])
        self.obj_group[-1].set_property('vert_uvs', vert_uvs)
    
    def handle_vertex_colors_block(self, file, count, size):
        colors = []
        for _ in range(count):
            #print(f"0x{file.tell():8X}")
            col_r = NikkiReader.map_range(NikkiReader.read_float(file), 0.0, 255.0, 0.0, 1.0)
            col_g = NikkiReader.map_range(NikkiReader.read_float(file), 0.0, 255.0, 0.0, 1.0)
            col_b = NikkiReader.map_range(NikkiReader.read_float(file), 0.0, 255.0, 0.0, 1.0)
            col_a = NikkiReader.map_range(NikkiReader.read_float(file), 0.0, 255.0, 0.0, 1.0)
            colors.append([col_r,col_g,col_b,col_a])
        self.obj_group[-1].set_property('vert_cols', colors)
    
    def handle_vertex_weights_block(self, file, count, size):
        vert_weights = []

        for _ in range(count):
            pair_count = NikkiReader.read_uint32(file)
            weight_pairs = [[NikkiReader.read_uint32(file), NikkiReader.read_float(file) / 100] for _ in range(pair_count)]
            vert_weights.append(weight_pairs)
        
        self.obj_group[-1].set_property('vert_weights', vert_weights)

    def handle_material_data_block(self, file, count, size):
        for n in range(count):
            mat = MeshClass(name="AMO Material {n}")
            mat.set_property('unk1', NikkiReader.read_uint32(file))
            mat.set_property('unk2', NikkiReader.read_uint32(file))
            mat.set_property('unk3', NikkiReader.read_uint32(file))
            mat.set_property('emission', NikkiReader.read_vec4(file))
            mat.set_property('rgba1', NikkiReader.read_vec4(file))
            mat.set_property('rgba2', NikkiReader.read_vec4(file))
            mat.set_property('unk4', NikkiReader.read_float(file))
            mat.set_property('unk5', NikkiReader.read_uint32(file))
            mat.set_property('unkChunk', file.read(200))
            mat.set_property('texture', NikkiReader.read_uint32(file))
            self.mat_group.append(mat)
    
    def handle_texture_data_block(self, file, count, size):
        for n in range(count):
            tex = MeshClass(name=f"AMO Texture {n}")
            tex.set_property('tex_type', NikkiReader.read_uint32(file))
            tex.set_property('tex_count', NikkiReader.read_uint32(file))
            tex.set_property('tex_size', NikkiReader.read_uint32(file))
            tex.set_property('tex_id', NikkiReader.read_uint32(file))
            tex.set_property('tex_width', NikkiReader.read_uint32(file))
            tex.set_property('tex_height', NikkiReader.read_uint32(file))
            tex.set_property('unkChunk', file.read(244))
            self.tex_group.append(tex)
    
    def handle_renderflag_block(self, file, count, size):
        self.obj_group[-1].set_property('render_unk1', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk2', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk3', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk4', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk5', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk6', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk7', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk8', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk9', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk10', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk11', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_alpha', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk13', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk14', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk15', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk16', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk17', NikkiReader.read_uint32(file))
        self.obj_group[-1].set_property('render_unk18', NikkiReader.read_uint32(file))

    def handle_unknown_block(self, file, count, size):
        print("Unknown Block encountered. Skipping...")
        file.seek(size - 12, 1)
        '''
class amo_reader():
    obj_group = []
    mat_group = []
    tex_group = []

    sub_offsets = []
    sub_sizes = []

    def read_block(self, file):
        block_pos = file.tell()
        block_id = NikkiReader.read_uint32(file)
        block_count = NikkiReader.read_uint32(file)
        block_size = NikkiReader.read_uint32(file)
        match block_id:
            case 0x20000:
                print(f"Header Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                unk = NikkiReader.read_uint32(file)
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
                        if NikkiReader._big_endian:
                            unk_val = NikkiReader.read_uint16(file)
                            face_count = NikkiReader.read_uint16(file)
                        else:
                            face_count = NikkiReader.read_uint16(file)
                            unk_val = NikkiReader.read_uint16(file)
                        vertices = []
                        for i in range(face_count):
                            if file.tell() < max_pos:
                                vertices.append(NikkiReader.read_uint32(file))
                        strips.append(vertices)
                self.obj_group[-1].set_property('strips',strips)
            case 0x040000:
                print("Face Sub-Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                max_pos = (file.tell()+block_size)-12
                strips = []
                for n in range(block_count):
                    if file.tell() < max_pos:
                        if NikkiReader._big_endian == True:
                            unk_val = NikkiReader.read_uint16(file)
                            face_count = NikkiReader.read_uint16(file)
                        else:
                            face_count = NikkiReader.read_uint16(file)
                            unk_val = NikkiReader.read_uint16(file)
                        vertices = []
                        for i in range(face_count):
                            vertices.append(NikkiReader.read_uint32(file))
                        strips.append(vertices)
                self.obj_group[-1].set_property('strips2',strips)
            case 0x050000: # Unknown
                print("Material Remap Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                remaps = []
                for n in range(block_count):
                    remaps.append(NikkiReader.read_uint32(file))
                self.obj_group[-1].set_property('mat_remaps',remaps)
            case 0x060000: # Unknown
                print("Material Index Buffer Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                mat_buffer = []
                for n in range(block_count):
                    mat_buffer.append(NikkiReader.read_uint32(file))
                self.obj_group[-1].set_property('mat_buffer',mat_buffer)
            case 0x070000:
                print("Vertex Buffer Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                vert_buffer = []
                for n in range(block_count):
                    vert_buffer.append(NikkiReader.read_vec3(file))
                self.obj_group[-1].set_property('vert_buffer',vert_buffer)
            case 0x080000:
                print("Vertex Normals Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                vert_normals = []
                for n in range(block_count):
                    vert_normals.append(NikkiReader.read_vec3(file))
                self.obj_group[-1].set_property('vert_normals',vert_normals)
            case 0x0A0000:
                print("Vertex UVs Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                vert_uvs = []
                for n in range(block_count):
                    vert_uvs.append(NikkiReader.read_vec2(file))
                self.obj_group[-1].set_property('vert_uvs',vert_uvs)
            case 0x0B0000:
                print("Vertex Colors Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                vert_cols = []
                for n in range(block_count):
                    vert_cols.append(NikkiReader.read_vec4(file))
                self.obj_group[-1].set_property('vert_cols',vert_cols)
            case 0x0C0000:
                print("Vertex Weights Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                vert_weights = []
                for n in range(block_count):
                    pair_count = NikkiReader.read_uint32(file)
                    weight_pair = []
                    for i in range(pair_count):
                        wt_bone = NikkiReader.read_uint32(file)
                        wt_factor = NikkiReader.read_float(file) # Game uses range 0.0 - 100.0
                        weight_pair.append([wt_bone, wt_factor/100])
                    vert_weights.append(weight_pair)
                self.obj_group[-1].set_property('vert_weights',vert_weights)
            case 0x9:
                print("Material Data Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                for n in range(block_count):
                    self.mat_group.append(meshClass(name=f"AMO Material {n}"))
                    self.mat_group[-1].set_property('unk1',NikkiReader.read_uint32(file))
                    self.mat_group[-1].set_property('unk2',NikkiReader.read_uint32(file))
                    self.mat_group[-1].set_property('unk3',NikkiReader.read_uint32(file))
                    self.mat_group[-1].set_property('emission',NikkiReader.read_vec4(file))
                    self.mat_group[-1].set_property('rgba1',NikkiReader.read_vec4(file))
                    self.mat_group[-1].set_property('rgba2',NikkiReader.read_vec4(file))
                    self.mat_group[-1].set_property('unk4',NikkiReader.read_float(file))
                    self.mat_group[-1].set_property('unk5',NikkiReader.read_uint32(file))
                    self.mat_group[-1].set_property('unkChunk',file.read(200))
                    self.mat_group[-1].set_property('texture',NikkiReader.read_uint32(file))
            case 0xA:
                print("Texture Data Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                for n in range(block_count):
                    self.tex_group.append(meshClass(name=f"AMO Texture {n}"))
                    self.tex_group[-1].set_property('tex_type',NikkiReader.read_uint32(file))
                    self.tex_group[-1].set_property('tex_count',NikkiReader.read_uint32(file))
                    self.tex_group[-1].set_property('tex_size',NikkiReader.read_uint32(file))
                    self.tex_group[-1].set_property('tex_id',NikkiReader.read_uint32(file))
                    self.tex_group[-1].set_property('tex_width',NikkiReader.read_uint32(file))
                    self.tex_group[-1].set_property('tex_height',NikkiReader.read_uint32(file))
                    self.tex_group[-1].set_property('unkChunk',file.read(244))
            case _:
                print("Unknown Block")
                print(f"{block_pos:8X} | {block_id:8X} | {block_count:8X} | {block_size:8X}")
                file.seek(block_size-12,1)
        return
    '''
    def parse_tristrip(self,tri_strip):
        faces = []
        
        for n in tri_strip:
            for i in range(len(n) -2):
                if i % 2 == 0:
                    faces.append([n[i],n[i+1],n[i+2]])
                else:
                    faces.append([n[i],n[i+2],n[i+1]])
        
        return faces
    
    def load_amo(self, file, filename):
        file.seek(0,0)

        amo_header = NikkiReader.read_uint32(file)
        amo_version = NikkiReader.read_uint32(file)
        amo_size = NikkiReader.read_uint32(file)

        print(amo_size)
        while(file.tell() < amo_size):
            self.read_block(file)
        
        mat_names = self.create_materials(filename,self.mat_group)

        self.create_meshes(filename,mat_names)

    def create_materials(self, filename, material_groups):
        mat_names = []
        for idx, amo_mat in enumerate(material_groups):
            material = bpy.data.materials.new(name=f"{filename} Material {idx}")
            material.use_nodes = True
            material.use_backface_culling = False
            material.blend_method = 'HASHED'
            material.shadow_method = 'HASHED'
            material.amh_diffuse = amo_mat.get_property('rgba1')
            material.amh_ambient = amo_mat.get_property('rgba2')
            node_tree = material.node_tree
            nodes = node_tree.nodes
            links = node_tree.links

            mat_names.append(material.name)
            
            for node in nodes:
                nodes.remove(node)
                
            output_node = nodes.new(type='ShaderNodeOutputMaterial')
            output_node.location = (900,0)
                
            diffuse_node = nodes.new(type='ShaderNodeBsdfPrincipled')
            diffuse_node.name = "AMO BSDF"
            diffuse_node.location = (500,0)
            diffuse_node.inputs['Roughness'].default_value = 1.0
            
            mat_texture = self.tex_group[amo_mat.get_property('texture')].get_property('tex_id')
            texture_node = nodes.new(type='ShaderNodeTexImage')
            texture_node.name = "AMO Texture"
            texture_node.location = (0,0)
            if self.image_names:
                texture = bpy.data.images.get(self.image_names[mat_texture])
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
            alphamix_node.name = "AMO Alpha Mix"
            alphamix_node.location = (300,-300)
            alphamix_node.operation = 'MULTIPLY'
            
            links.new(texture_node.outputs['Color'],mix_node.inputs['A'])
            links.new(vertcol_node.outputs['Color'],mix_node.inputs['B'])
            links.new(mix_node.outputs['Result'],diffuse_node.inputs[0])
            links.new(mix_node.outputs['Result'],diffuse_node.inputs[26])
            links.new(vertcol_node.outputs['Alpha'],alphamix_node.inputs[0])
            links.new(texture_node.outputs['Alpha'],alphamix_node.inputs[1])
            links.new(alphamix_node.outputs[0],diffuse_node.inputs[4])
            links.new(diffuse_node.outputs['BSDF'],output_node.inputs['Surface'])
            
            if self.ignore_emissive == False:
                color_emit = amo_mat.get_property('emission')
                avg_emit = (color_emit[0] + color_emit[1] + color_emit[2]) / 3
                maprange_node = nodes.new(type='ShaderNodeMapRange')
                maprange_node.location = (300,-600)
                maprange_node.inputs[0].default_value = avg_emit
                maprange_node.inputs[1].default_value = 0
                maprange_node.inputs[2].default_value = 1
                maprange_node.inputs[3].default_value = -1
                maprange_node.inputs[4].default_value = 1
                links.new(maprange_node.outputs[0],diffuse_node.inputs[27])
        return mat_names
    
    def create_meshes(self, filename, materials):
        for amo_obj in self.obj_group:
            all_strips = amo_obj.get_property('strips') + amo_obj.get_property('strips2')
            faces = self.parse_tristrip(all_strips)
            
            mesh = bpy.data.meshes.new(amo_obj.name)
            obj = bpy.data.objects.new(f"{filename} {amo_obj.name}", mesh)
            col = bpy.data.collections[0]

            obj.visible_shadow = False
            obj.visible_diffuse = False
            if self.rotate_delta:
                obj.delta_rotation_euler[0] = math.radians(90)
            
            col.objects.link(obj)
            bpy.context.view_layer.objects.active = obj
                
            mesh.from_pydata(amo_obj.get_property('vert_buffer'), [], faces)

            bm = bmesh.new()
            bm.from_mesh(mesh)

            custom_index_layer = bm.verts.layers.int.new('custom_index')

            for i, v in enumerate(bm.verts):
                v[custom_index_layer] = i
            
            bm.to_mesh(mesh)
            bm.free()

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
            for idx, strip in enumerate(amo_obj.get_property('strips')):
                strip_name = f"Strip1.{str(idx).zfill(3)}"
                if strip_name not in obj.vertex_groups:
                    vertex_group = obj.vertex_groups.new(name=strip_name)
                    weight = 1/len(strip)
                    for vert in strip:
                        vertex_group.add([vert], weight, 'REPLACE')

            for idx, strip in enumerate(amo_obj.get_property('strips2')):
                strip_name = f"Strip2.{str(idx).zfill(3)}"
                if strip_name not in obj.vertex_groups:
                    vertex_group = obj.vertex_groups.new(name=strip_name)
                    weight = 1/len(strip)
                    for vert in strip:
                        vertex_group.add([vert], weight, 'REPLACE')
            
            for mat_id in amo_obj.get_property('mat_remaps'):
                mat_name = materials[mat_id]
                mat_ref = bpy.data.materials.get(mat_name)
                
                if mat_name not in obj.data.materials:
                    obj.data.materials.append(mat_ref)
            
            for idx, mat_id in enumerate(amo_obj.get_property('mat_buffer')):
                strip_name = f"Strip1.{str(idx).zfill(3)}"
                vert_group = obj.vertex_groups.get(strip_name)

                if vert_group:
                    group_index = vert_group.index
                    group_verts = [v.index for v in obj.data.vertices if group_index in [g.group for g in v.groups]]
                    
                    for poly in obj.data.polygons:
                        if any(v in group_verts for v in poly.vertices):
                            poly.select = True
                            poly.material_index = mat_id
                        else:
                            poly.select = False
            
            for idx, mat_id in enumerate(amo_obj.get_property('mat_buffer')):
                strip_name = f"Strip2.{str(idx).zfill(3)}"
                vert_group = obj.vertex_groups.get(strip_name)

                if vert_group:
                    group_index = vert_group.index
                    group_verts = [v.index for v in obj.data.vertices if group_index in [g.group for g in v.groups]]
                    
                    for poly in obj.data.polygons:
                        if any(v in group_verts for v in poly.vertices):
                            poly.select = True
                            poly.material_index = mat_id
                        else:
                            poly.select = False
            
            print(amo_obj.get_property('render_alpha'))

            if self.ignore_additive == False and amo_obj.get_property('render_alpha') == 2:
                for material in obj.data.materials:
                    texNode = material.node_tree.nodes.get("AMO Texture")
                    mixNode = material.node_tree.nodes.get("AMO Alpha Mix")

                    material.node_tree.links.new(texNode.outputs['Color'],mixNode.inputs[1])