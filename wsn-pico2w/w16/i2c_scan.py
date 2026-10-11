import myid                      # 身份指紋（第一行；A、B 兩片都跑一次）
# 整合任何 I2C 模組的第一步：先確認掃得到
from machine import Pin, I2C

i2c0 = I2C(0, scl=Pin(5), sda=Pin(4), freq=100_000)
i2c1 = I2C(1, scl=Pin(7), sda=Pin(6), freq=100_000)

for name, bus in (('I2C0', i2c0), ('I2C1', i2c1)):
    found = bus.scan()
    print(name, '找到', len(found), '個裝置')
    for a in found:
        print('   位址', hex(a))

# 掃不到就回頭量電壓與共地，不要急著改程式
