def grain(x: int, y: int, salt: int) -> int:
    value = x * 374761393 + y * 668265263 + salt * 2246822519
    value = (value ^ (value >> 13)) * 1274126177
    return (value ^ (value >> 16)) & 0xFFFFFFFF
