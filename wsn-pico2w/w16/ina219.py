# ina219.py：INA219（I2C 0x40）的最小驅動，直接讀寫暫存器
R_SHUNT = 0.1                    # 模組上的分流電阻 0.1 Ω（板上印 R100）
LSB_MA = 0.01 / R_SHUNT          # 1 LSB＝10 µV：0.01 mV ÷ 0.1 Ω＝0.1 mA
CONFIG = 0x01E7                  # 16 V、±40 mV、分流 16 次平均、連續量


class INA219:
    def __init__(self, i2c, zero_ma=0.0, addr=0x40):
        self.i2c, self.addr, self.zero = i2c, addr, zero_ma
        self.write(0x00, CONFIG)             # 寫設定暫存器
    def write(self, reg, val):               # 寫 16 位元：高位元組先送
        self.i2c.writeto_mem(self.addr, reg, bytes((val >> 8, val & 0xFF)))
    def read(self, reg):                     # 讀 16 位元：高位元組在前
        b = self.i2c.readfrom_mem(self.addr, reg, 2)
        return (b[0] << 8) | b[1]

    def shunt_raw(self):                     # 0x01 分流電壓（有號數）
        v = self.read(0x01)
        return v - 65536 if v & 0x8000 else v
    def ma(self, raw):                       # 原始值換成 mA，扣掉零點
        return raw * LSB_MA - self.zero
    def current_ma(self):                    # I＝V÷R（歐姆定律）
        return self.ma(self.shunt_raw())
    def bus_v(self):                         # 0x02 匯流排電壓，1 LSB＝4 mV
        return (self.read(0x02) >> 3) * 0.004
