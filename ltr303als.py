# The MIT License (MIT)
#
# Copyright (c) 2020 arturo182
# Copyright (c) 2019 ladyada for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import time
from adafruit_register.i2c_bit import RWBit, ROBit
from adafruit_register.i2c_bits import RWBits
from adafruit_bus_device.i2c_device import I2CDevice
from micropython import const

GAIN_1X = 0
GAIN_2X = 1
GAIN_4X = 2
GAIN_8X = 3
GAIN_48X = 6
GAIN_96X = 7

INTEGRATION_TIME_100MS = 0
INTEGRATION_TIME_50MS = 1
INTEGRATION_TIME_200MS = 2
INTEGRATION_TIME_400MS = 3
INTEGRATION_TIME_150MS = 4
INTEGRATION_TIME_250MS = 5
INTEGRATION_TIME_300MS = 6
INTEGRATION_TIME_350MS = 7

MEASUREMENT_RATE_50MS = 0
MEASUREMENT_RATE_100MS = 1
MEASUREMENT_RATE_200MS = 2
MEASUREMENT_RATE_500MS = 3
MEASUREMENT_RATE_1000MS = 4
MEASUREMENT_RATE_2000MS = 5


_LTR303ALS_CONTR = const(0x80)
_LTR303ALS_MEAS_RATE = const(0x85)
_LTR303ALS_PART_ID = const(0x86)
_LTR303ALS_MANU_ID = const(0x87)
_LTR303ALS_DATA_CH1_0 = const(0x88)
_LTR303ALS_DATA_CH1_1 = const(0x89)
_LTR303ALS_DATA_CH0_0 = const(0x8A)
_LTR303ALS_DATA_CH0_1 = const(0x8B)
_LTR303ALS_STATUS = const(0x8C)
_LTR303ALS_INTERRUPT = const(0x8F)
_LTR303ALS_THRES_UP_0 = const(0x97)
_LTR303ALS_THRES_UP_1 = const(0x98)
_LTR303ALS_THRES_LOW_0 = const(0x99)
_LTR303ALS_THRES_LOW_1 = const(0x9A)
_LTR303ALS_INTERRUPT_PERSIST = const(0x9E)


class LTR303ALS:
    mode = RWBit(_LTR303ALS_CONTR, 0)
    sw_reset = RWBit(_LTR303ALS_CONTR, 1)
    gain = RWBits(3, _LTR303ALS_CONTR, 2)

    measurement_rate = RWBits(3, _LTR303ALS_MEAS_RATE, 0)
    integration_time = RWBits(3, _LTR303ALS_MEAS_RATE, 3)

    data_status = RWBit(_LTR303ALS_STATUS, 2)
    interrupt_status = RWBit(_LTR303ALS_STATUS, 3)
    data_valid = RWBit(_LTR303ALS_STATUS, 7)

    def __init__(self, i2c_bus, device_address=0x29):
        self.i2c_device = I2CDevice(i2c_bus, device_address)
        self._buf = bytearray(3)

        _id = self._read_register(_LTR303ALS_PART_ID)[0]
        if _id != 0xA0:
            raise ValueError('Unable to find LTR303-ALS at i2c address %s' % hex(address))

        self.reset()

    @property
    def lux(self):
        gain_values = [1, 2, 4, 8, 0, 0, 48, 96]
        int_values = [1, 0.5, 2, 4, 1.5, 2.5, 3, 3.5]

        data0_0, data0_1 = self._read_register(_LTR303ALS_DATA_CH0_0, 2)
        data1_0, data1_1 = self._read_register(_LTR303ALS_DATA_CH1_0, 2)

        data0 = (data0_1 << 8) | data0_0
        data1 = (data1_1 << 8) | data1_0

        ratio = data1 / (data0 + data1)
        p_factor = 1.0
        gain_x = gain_values[self.gain]
        int_ms = int_values[self.integration_time]

        # Based on LTR-303ALS Appendix A
        lux = 0
        if ratio < 0.45:
            lux = (1.7743 * data0 + 1.1059 * data1) / gain_x / int_ms / p_factor
        elif ratio < 0.64:
            lux = (4.2785 * data0 - 1.9548 * data1) / gain_x / int_ms / p_factor
        elif ratio < 0.85:
            lux = (0.5926 * data0 + 0.1185 * data1) / gain_x / int_ms / p_factor

        return lux

    def reset(self):
        self.sw_reset = 1
        while self.sw_reset:
            time.sleep(0.2)

        self.mode = 1
        time.sleep(0.2)

    def _read_register(self, addr, num=1):
        self._buf[0] = addr
        with self.i2c_device as i2c:
            i2c.write_then_readinto(self._buf, self._buf, out_end=1, in_start=1, in_end=num + 1)
        return self._buf[1 : num + 1]

    def _write_register(self, addr, data=None):
        self._buf[0] = addr
        end = 1
        if data:
            self._buf[1] = data
            end = 2
        with self.i2c_device as i2c:
            i2c.write(self._buf, end=end)
