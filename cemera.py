import sensor, image, time

# —— 摄像头初始化 —— #
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)  # 灰度模式
sensor.set_framesize(sensor.QQVGA)      # 160×120
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)

# —— 矩形动态识别参数 —— #
RECT_THRESHOLD       = 12000
RECT_GRADIENT        = 10
MAX_HISTORY          = 3
INIT_CONFIRM_THRESH  = 3
RECT_INIT_DIST       = 20
RECT_TRACK_DIST      = 30

# —— 状态变量 —— #
first_rect_corners = [[0, 0] for _ in range(4)]
history_corners     = []
init_confirm_count  = 0

# —— 辅助函数 —— #
def get_rect_center(corners):
    cx = sum(p[0] for p in corners) // 4
    cy = sum(p[1] for p in corners) // 4
    return (cx, cy)

def rect_distance(c1, c2):
    x1, y1 = get_rect_center(c1)
    x2, y2 = get_rect_center(c2)
    return ((x1 - x2)**2 + (y1 - y2)**2)**0.5

# —— 主循环 —— #
clock = time.clock()
while True:
    clock.tick()
    img = sensor.snapshot()

    # 1) 找到第一个矩形
    current_rect = None
    for r in img.find_rects(threshold=RECT_THRESHOLD,
                            x_gradient=RECT_GRADIENT,
                            y_gradient=RECT_GRADIENT):
        current_rect = r
        break

    # 2) 初始化确认 & 跟踪更新
    if current_rect:
        new_corners = current_rect.corners()
        # 初始确认阶段
        if first_rect_corners == [[0, 0]]*4:
            if not history_corners:
                history_corners.append(new_corners)
                init_confirm_count = 1
            else:
                if rect_distance(new_corners, history_corners[-1]) < RECT_INIT_DIST:
                    init_confirm_count += 1
                    history_corners.append(new_corners)
                    if init_confirm_count >= INIT_CONFIRM_THRESH:
                        first_rect_corners = new_corners
                else:
                    init_confirm_count = 1
                    history_corners = [new_corners]
        # 跟踪阶段
        else:
            if rect_distance(new_corners, first_rect_corners) < RECT_TRACK_DIST:
                first_rect_corners = new_corners
                history_corners.append(new_corners)
                if len(history_corners) > MAX_HISTORY:
                    history_corners.pop(0)

    # 3) 可视化跟踪到的矩形
    if first_rect_corners != [[0, 0]]*4:
        for i in range(4):
            x1, y1 = first_rect_corners[i]
            x2, y2 = first_rect_corners[(i+1) % 4]
            img.draw_line(x1, y1, x2, y2)

    print("FPS:", clock.fps())
