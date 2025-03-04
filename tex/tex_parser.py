import bpy
import io
import numpy as np

from ..helpers.nikkireader import NikkiReader

def pal_rgba32(apx):
    if NikkiReader._big_endian:
        c_a = NikkiReader.read_byte(apx) / 255.0
        c_b = NikkiReader.read_byte(apx) / 255.0
        c_g = NikkiReader.read_byte(apx) / 255.0
        c_r = NikkiReader.read_byte(apx) / 255.0
    else:
        c_r = NikkiReader.read_byte(apx) / 255.0
        c_g = NikkiReader.read_byte(apx) / 255.0
        c_b = NikkiReader.read_byte(apx) / 255.0
        c_a = NikkiReader.read_byte(apx) / 255.0
    return [c_r,c_g,c_b,c_a]

def pal_rgba16(apx):
    if NikkiReader._big_endian:
        c_a = NikkiReader.read_uint4(apx,True) / 255.0
        apx.seek(-1,1)
        c_b = NikkiReader.read_uint4(apx) / 255.0
        c_g = NikkiReader.read_uint4(apx,True) / 255.0
        apx.seek(-1,1)
        c_r = NikkiReader.read_uint4(apx) / 255.0
    else:
        c_r = NikkiReader.read_uint4(apx) / 255.0
        apx.seek(-1,1)
        c_g = NikkiReader.read_uint4(apx,True) / 255.0
        c_b = NikkiReader.read_uint4(apx) / 255.0
        apx.seek(-1,1)
        c_a = NikkiReader.read_uint4(apx,True) / 255.0
    return [c_r,c_g,c_b,c_a]

def apx_decode(apx, idx):
    apx_pixelcount = NikkiReader.read_uint32(apx)
    pal_size = NikkiReader.read_uint32(apx)
    apx_bitdepth = NikkiReader.read_uint16(apx)
    apx_width = NikkiReader.read_uint16(apx)
    apx_height = NikkiReader.read_uint16(apx)
    apx_index = NikkiReader.read_uint16(apx)
    pal_bitdepth = NikkiReader.read_uint16(apx)
    pal_index = NikkiReader.read_uint16(apx)
    unk1 = NikkiReader.read_uint32(apx)
    unk2 = NikkiReader.read_uint32(apx)
        
    palette_data = []
    image_data = np.zeros((apx_height,apx_width,4), dtype=np.float32)
    
    apx_imgOfs = apx.tell()
    
    apx.seek(apx_pixelcount,1)
    
    if pal_bitdepth == 32:
        for n in range(pal_size//4):
            palette_data.append(pal_rgba32(apx))
    elif pal_bitdepth == 16:
        for n in range(pal_size//2):
            palette_data.append(pal_rgba16(apx))
    else:
        print(f"Palette Bit Depth = {pal_bitdepth}")
    
    apx.seek(apx_imgOfs)
    if apx_bitdepth == 8:
        for y in range(apx_height):
            for x in range(apx_width):
                palid = NikkiReader.read_byte(apx)
                color = palette_data[palid]
                image_data[apx_height - y - 1, x] = color  # Flip Y correctly

    elif apx_bitdepth == 4:
        for y in range(apx_height):
            for x in range(apx_width):
                if x % 2 == 0:
                    palid = NikkiReader.read_uint4(apx)
                    apx.seek(-1,1)
                else:
                    palid = NikkiReader.read_uint4(apx, True)
                color = palette_data[palid]
                image_data[apx_height - y - 1, x] = color  # Flip Y correctly
    else:
        print(f"Image Bit Depth = {apx_bitdepth} at {apx.tell():8X}")
        
    flattened_data = image_data.flatten()
    
    image = bpy.data.images.new(f"Tex Image {idx}", width=apx_width, height=apx_height)
    image.pixels = flattened_data.tolist()
    image.update
    return image

def parse_tex(filepath):
    images = []

    file_meta = []

    with open(filepath, 'rb') as file:
        file_count = NikkiReader.read_uint32(file)
        '''
        if file_count >= 16777216:
            big_endian = True
            file.seek(0)
            file_count = read_uint32(file)
        '''
        for n in range(file_count):
            # Offset and Size
            ptr = NikkiReader.read_uint32(file)
            size = NikkiReader.read_uint32(file)
            file_meta.append([ptr,size])
        
        for idx, subfile in enumerate(file_meta):
            apx = NikkiReader.create_subfile(file, subfile[0], subfile[1])
            apx_size = NikkiReader.read_uint32(apx)
            image = apx_decode(apx, idx)
            images.append(image.name)
    return images