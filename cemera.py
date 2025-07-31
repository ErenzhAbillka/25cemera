import sensor, image, time, math

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
sensor.set_auto_exposure(False, exposure_us=20000)  # 手动曝光 20 ms

RECT_THRESHOLD    = 12000
INIT_FRAMES       = 3
TRACK_DIST_SQR    = 30**2
LOSE_RESET_FRAMES = 5

A4_RATIO = math.sqrt(2)        # ≈1.414
RATIO_TOL = 0.1                # ±10% 容差，可根据实际调小到 ±5% (0.05)

history   = []                  # 用于确认目标
confirmed = None
conf_cnt  = 0
lose_cnt  = 0

clock = time.clock()
while True:
    clock.tick()
    img = sensor.snapshot()

    rects = img.find_rects(threshold = RECT_THRESHOLD)
    if rects:
        lose_cnt = 0
        # 遍历所有候选，挑最符合 A4 纸比例的
        best = None
        best_diff = 1e6
        for r in rects:
            w, h = r.w(), r.h()
            aspect = max(w, h) / float(min(w, h))
            diff = abs(aspect - A4_RATIO)
            if diff < best_diff:
                best_diff = diff
                best = (r, w, h, aspect, diff)

        # 如果最优候选足够接近，再“确认”它
        r, w, h, aspect, diff = best
        if diff < RATIO_TOL:
            x, y = r.x(), r.y()
            cx, cy = x + w//2, y + h//2

            if confirmed is None:
                history.append((cx, cy))
                conf_cnt += 1
                if conf_cnt >= INIT_FRAMES:
                    confirmed = (cx, cy)
            else:
                px, py = confirmed
                if (cx-px)**2 + (cy-py)**2 < TRACK_DIST_SQR:
                    confirmed = (cx, cy)
        else:
            # 没有合格的 A4 候选，视为“没检测到”
            rects = []

    else:
        lose_cnt += 1
        if lose_cnt >= LOSE_RESET_FRAMES:
            confirmed = None
            history.clear()
            conf_cnt = lose_cnt = 0

    if confirmed:
        cx, cy = confirmed
        img.draw_rectangle((cx - w//2, cy - h//2, w, h))
        img.draw_cross(cx, cy)
        print("A4 Center:", cx, cy, "Aspect:", aspect)
