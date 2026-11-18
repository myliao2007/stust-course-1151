# bmp280.py：BMP280 氣壓／溫度的小驅動（照 Bosch 規格書的補償公式）
import struct


class BMP280:
    def __init__(self, i2c, addr=0x76):
        self.i2c, self.addr = i2c, addr
        if i2c.readfrom_mem(addr, 0xD0, 1)[0] != 0x58:
            raise OSError("找不到 BMP280（晶片 ID 不是 0x58）")
        c = struct.unpack("<HhhHhhhhhhhh", i2c.readfrom_mem(addr, 0x88, 24))
        self.t1, self.t2, self.t3 = c[0], c[1], c[2]
        self.p = c[3:]
        i2c.writeto_mem(addr, 0xF5, b"\x00")   # 不濾波
        i2c.writeto_mem(addr, 0xF4, b"\x27")   # 溫度×1、氣壓×1、連續量

    def compensate(self, adc_t, adc_p):
        v1 = (adc_t / 16384 - self.t1 / 1024) * self.t2
        v2 = (adc_t / 131072 - self.t1 / 8192) ** 2 * self.t3
        t_fine = v1 + v2
        temp = t_fine / 5120
        p1, p2, p3, p4, p5, p6, p7, p8, p9 = self.p
        v1 = t_fine / 2 - 64000
        v2 = v1 * v1 * p6 / 32768 + v1 * p5 * 2
        v2 = v2 / 4 + p4 * 65536
        v1 = (p3 * v1 * v1 / 524288 + p2 * v1) / 524288
        v1 = (1 + v1 / 32768) * p1
        if v1 == 0:
            return temp, 0
        pa = 1048576 - adc_p
        pa = (pa - v2 / 4096) * 6250 / v1
        v1 = p9 * pa * pa / 2147483648
        v2 = pa * p8 / 32768
        pa = pa + (v1 + v2 + p7) / 16
        return temp, pa

    def read(self):
        d = self.i2c.readfrom_mem(self.addr, 0xF7, 6)
        adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
        adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
        return self.compensate(adc_t, adc_p)
