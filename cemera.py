import sensor, image, time
from vuui import SMC
from pyb import UART

# UART 设置
uart = UART(1, 9600)
uart.init(9600, bits=8, parity=None, stop=1)

# SMC 控制器
pan_SMC  = SMC(5, 50, 50, 3)
tilt_SMC = SMC(5, 50, 50, 3)

# 摄像头初始化
sensor.reset()
sensor.set_contrast(3)
sensor.set_gainceiling(16)
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(False)
sensor.skip_frames(10)
sensor.set_auto_exposure(False, exposure_us = 30000)
sensor.set_auto_whitebal(False)
clock = time.clock()

def find_max(blobs):
    max_size = 0
    max_blob = None
    for blob in blobs:
        size = blob.w() * blob.h()
        if size > max_size:
            max_blob = blob
            max_size = size
    return max_blob

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def send_uart_packet(uart, pan_U_abs, pan_U_sign, tilt_U_abs, tilt_U_sign):
    pan_U_sign = 0 if pan_U_sign < 0 else 1
    tilt_U_sign = 0 if tilt_U_sign < 0 else 1
    packet = bytearray([
        0x2C, 0x04,
        int(pan_U_abs) & 0xFF,
        int(pan_U_sign) & 0xFF,
        int(tilt_U_abs) & 0xFF,
        int(tilt_U_sign) & 0xFF,
        0x5B
    ])
    uart.write(packet)
#   print("Sent Packet:", list(packet))

# ==============================
# 主循环
# ==============================
if __name__ == "__main__":
    while True:
        clock.tick()
        img = sensor.snapshot()

        # 1. 二值化
        binary_img = img.to_grayscale().binary([(0, 100)])  # 你可以调节阈值

        # 2. 动态识别矩形
        rects = binary_img.find_rects(threshold=10000)  # 可调阈值
        for r in rects:
            img.draw_rectangle(r.rect(), color=(255, 0, 0))
            img.draw_cross(r.cx(), r.cy(), color=(255, 0, 0))

            # 使用矩形中心作为控制目标
            redx = r.cx()
            greenx = img.width() // 2  # 可替换为其他参考点
            # pan_SMC.sliding_mode_init(greenx, redx)
            # pan_SMC.sliding_mode_control_law()
            # pan_U_abs, pan_U_sign = pan_SMC.get_control_input()

            # 示例用固定值发送 tilt 参数
            # send_uart_packet(uart, pan_U_abs, pan_U_sign, 0, 0)

        # 3. （可选）使用颜色追踪
        # redx, redy = find_color_threshold(img, (30, 100, 30, 127, 0, 127))  # 例：红色激光
