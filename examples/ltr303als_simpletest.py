from ltr303als import LTR303ALS, GAIN_4X, INTEGRATION_TIME_50MS, MEASUREMENT_RATE_50MS
import board
import time

i2c = board.I2C()
ltr = LTR303ALS(i2c)

ltr.gain = GAIN_4X
ltr.integration_time = INTEGRATION_TIME_50MS
ltr.measurement_rate = MEASUREMENT_RATE_50MS

while True:
    print('Lux: %d' % ltr.lux);
    time.sleep(0.25)
