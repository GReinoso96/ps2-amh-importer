import struct

class NikkiReader:
    _big_endian = False

    @classmethod
    def set_endian(cls, big_endian: bool):
        cls._big_endian = big_endian
    
    @classmethod
    def _get_format(cls, fmt: str):
        endian_prefix = '>' if cls._big_endian else '<'
        return endian_prefix + fmt
    
    @classmethod
    def read_uint4(cls, file, half=False):
        byte_value = ord(file.read(1))
        return (byte_value >> 4) & 0xF if half else byte_value & 0xF
    
    @classmethod
    def read_byte(cls, file):
        return struct.unpack('B', file.read(1))[0]
    
    @classmethod
    def read_uint16(cls, file):
        return struct.unpack(cls._get_format('H'), file.read(2))[0]
    
    @classmethod
    def read_uint32(cls, file):
        return struct.unpack(cls._get_format('I'), file.read(4))[0]
    
    @classmethod
    def read_float(cls, file):
        return struct.unpack(cls._get_format('f'), file.read(4))[0]
    
    @classmethod
    def read_vec2(cls, file):
        return struct.unpack(cls._get_format('2f'), file.read(8))
    
    @classmethod
    def read_vec3(cls, file):
        return struct.unpack(cls._get_format('3f'), file.read(12))
    
    @classmethod
    def read_vec4(cls, file):
        return struct.unpack(cls._get_format('4f'), file.read(16))