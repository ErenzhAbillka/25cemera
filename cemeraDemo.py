import sensor, image, time

# 摄像头初始化
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_contrast(3)
sensor.set_gainceiling(16)
sensor.set_vflip(False)
sensor.skip_frames(10)
sensor.set_auto_exposure(False, exposure_us=30000)
sensor.set_auto_whitebal(False)
clock = time.clock()

while True:
    clock.tick()
    img = sensor.snapshot()

    # 转灰度图
    gray = img.to_grayscale()

    # 二值化：只保留黑色（0~20），其余全部设为白色255
    # invert=True 反转后：黑底变白，黑色区域才为255
    binary = gray.binary([(0, 20)], invert=True)

    # 形态学闭运算填补矩形边缘缺口（提高鲁棒性）
    binary.dilate(1)
    binary.erode(1)

    # 查找所有矩形
    rects = binary.find_rects(threshold=10000)

    if rects:
        # 选最大矩形（面积最大）
        outer_rect = max(rects, key=lambda r: r.w() * r.h())

        # 画红框
        img.draw_rectangle(outer_rect.rect(), color=(255, 0, 0))

        # 获取角点
        corners = outer_rect.corners()
        for p in corners:
            img.draw_cross(p[0], p[1], color=(0, 255, 0))  # 绿叉角点
        print("外部矩形角点坐标:", corners)

        # 中心点坐标（用 rect 中心）
        r = outer_rect.rect()  # (x, y, w, h)
        center_x = r[0] + r[2] // 2
        center_y = r[1] + r[3] // 2
        img.draw_cross(center_x, center_y, color=(255, 255, 255))  # 白叉中心
        print("中心点坐标: ({}, {})".format(center_x, center_y))
