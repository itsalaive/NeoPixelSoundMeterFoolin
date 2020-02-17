# The MIT License (MIT)
#
# Copyright (c) 2017 Dan Halbert for Adafruit Industries
# Copyright (c) 2017 Kattni Rembor, Tony DiCola for Adafruit Industries
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

# Circuit Playground Sound Meter

import array
import random
import math
import audiobusio
import board
import time
import neopixel

# Color of the peak pixel.
PEAK_COLOR = (100, 0, 255)
# Number of pixels on each Neopixel ring, starting with the onboard one
NUM_PIXELS = 10
NUM_PIXELS2 = 16
# Number of total pixels - 10 build into Circuit Playground, + however many extra neopixels you connect
TOT_PIXELS = 26

# Exponential scaling factor.
# Should probably be in range -10 .. 10 to be reasonable.
CURVE = 2
SCALE_EXPONENT = math.pow(10, CURVE * -0.1)

# Number of samples to read at once.
NUM_SAMPLES = 160


# Restrict value to be between floor and ceiling.
def constrain(value, floor, ceiling):
    return max(floor, min(value, ceiling))


# Scale input_value between output_min and output_max, exponentially.
def log_scale(input_value, input_min, input_max, output_min, output_max):
    normalized_input_value = (input_value - input_min) / \
                             (input_max - input_min)
    return output_min + \
        math.pow(normalized_input_value, SCALE_EXPONENT) \
        * (output_max - output_min)


# Remove DC bias before computing RMS.
def normalized_rms(values):
    minbuf = int(mean(values))
    samples_sum = sum(
        float(sample - minbuf) * (sample - minbuf)
        for sample in values
    )

    return math.sqrt(samples_sum / len(values))


def mean(values):
    return sum(values) / len(values)


def volume_color(volume, pixnum):
    return 200, volume * (255 // pixnum), 0






# Main program

# Set up NeoPixels and turn them all off.
pixels = neopixel.NeoPixel(board.NEOPIXEL, NUM_PIXELS, brightness=0.1, auto_write=False)
pixels2 = neopixel.NeoPixel(board.A2, NUM_PIXELS2, brightness=0.1, auto_write=False)
pixels.fill(0)
pixels2.fill(0)
pixels2.show()
pixels.show()

mic = audiobusio.PDMIn(board.MICROPHONE_CLOCK, board.MICROPHONE_DATA,
                       sample_rate=16000, bit_depth=16)

# Record an initial sample to calibrate. Assume it's quiet when we start.
samples = array.array('H', [0] * NUM_SAMPLES)
mic.record(samples, len(samples))
# Set lowest level to expect, plus a little.
input_floor = normalized_rms(samples) + 10
# OR: used a fixed floor
# input_floor = 50

# You might want to print the input_floor to help adjust other values.
# print(input_floor)

# Corresponds to sensitivity: lower means more pixels light up with lower sound
# Adjust this as you see fit.
input_ceiling = input_floor + 500




peak = 0
peak2 = 0
while True:
    mic.record(samples, len(samples))
    magnitude = normalized_rms(samples)
    # You might want to print this to see the values.
    print(magnitude)

    # Compute scaled logarithmic reading in the range 0 to NUM_PIXELS
    c = int(log_scale(constrain(magnitude, input_floor, input_ceiling),
                  input_floor, input_ceiling, 0, TOT_PIXELS))
#    c2 = log_scale(constrain(magnitude, input_floor, input_ceiling2),
#                  input_floor, input_ceiling2, 0, NUM_PIXELS2)
    print(c)

    # Light up pixels that are below the scaled and interpolated magnitude.
    pixels.fill(0)
    pixels2.fill(0)
    # Neopixels start at address 0, so we subtract 1 from the number of total pixels to accurately address the right pixels, otherwise it breaks!
    for i in range(TOT_PIXELS-1):
        if i < c:
            # If the Neopixel being addressed is over 9 it means it needs to start sending commands to the auxiliary Neopixel ring on A2
            if i > 9:
                # The Neopixels on the Board light up Anti-clockwise, so a simple math trick reverses the direction in which the auxiliary Neopixel Ring pixels light up create a continuous spiral effect.
                j = 15 - (i-10)
                pixels2[j] = volume_color(j, NUM_PIXELS2)
            else:
                pixels[i] = volume_color(i, NUM_PIXELS)
        # Light up the peak pixel and animate it slowly dropping.
        if c >= peak:
            peak = min(c, TOT_PIXELS - 1)
        elif peak > 0:
            peak = peak - 1
        # Sets up the Decay sequence to have the Neopixels turn off, once again addressing the Aux Neopixel Ring if the pixel being addressed is over 10
        if peak > 0:
            if peak > 9:
                peak2 = 15 - (peak-10)
                pixels2[int(peak2)] = PEAK_COLOR
            else:
                pixels[int(peak)] = PEAK_COLOR
    pixels.show()
    pixels2.show()