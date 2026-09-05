from termuxgui import Connection, Activity, LinearLayout, ImageView, Buffer
import time

c = Connection()
a = Activity(c)
root = LinearLayout(a, vertical=True)
root.setwidth(100, px=True)
root.setheight(100, px=True)
img = ImageView(a, parent=root)
img.setwidth(100, px=True)
img.setheight(100, px=True)

b = Buffer(c, 100, 100)
black = bytes((0, 0, 0, 255))
white = bytes((255, 255, 255, 255))
frame = bytearray(100 * 100 * 4)
for y in range(100):
    for x in range(100):
        off = (y * 100 + x) * 4
        frame[off:off+4] = white if 47 <= x <= 51 and 47 <= y <= 51 else black
b.mem[:] = frame
img.setbuffer(b)
b.blit()
img.refresh()
print('GUI ready')
while True:
    time.sleep(1)
