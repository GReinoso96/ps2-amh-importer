import struct

big_endian = False

def read_byte(file):
    value = file.read(1)
    return struct.unpack('B', value)[0]

def read_uint16(file):
    value = file.read(2)
    if big_endian == True:
        value = value[::-1]
    return struct.unpack('H', value)[0]

def read_uint32(file):
    value = file.read(4)
    if big_endian == True:
        value = value[::-1]
    return struct.unpack('I', value)[0]

def read_uint4(file,half=False):
    value = file.read(1)
    
    byte_value = ord(value)
    
    if half:
        return (byte_value >> 4) & 0xF
    else:
        return byte_value & 0xF

def read_float(file):
    value = file.read(4)
    if big_endian == True:
        value = value[::-1]
    return struct.unpack('f', value)[0]

def read_vec2(file):
    x = file.read(4)
    y = file.read(4)
    if big_endian == True:
        x = x[::-1]
        y = y[::-1]
    x = struct.unpack('f', x)[0]
    y = struct.unpack('f', y)[0]
    return (x, y)

def read_vec3(file):
    x = file.read(4)
    y = file.read(4)
    z = file.read(4)
    if big_endian == True:
        x = x[::-1]
        y = y[::-1]
        z = z[::-1]
    x = struct.unpack('f', x)[0]
    y = struct.unpack('f', y)[0]
    z = struct.unpack('f', z)[0]
    return (x, y, z)

def read_vec4(file):
    x = file.read(4)
    y = file.read(4)
    z = file.read(4)
    w = file.read(4)
    if big_endian == True:
        x = x[::-1]
        y = y[::-1]
        z = z[::-1]
        w = w[::-1]
    x = struct.unpack('f', x)[0]
    y = struct.unpack('f', y)[0]
    z = struct.unpack('f', z)[0]
    w = struct.unpack('f', w)[0]
    return (x, y, z, w)