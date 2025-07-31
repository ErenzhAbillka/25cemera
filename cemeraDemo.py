import sensor, image, time
from pyb import Timer, Pin
from SMC import SMC

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
sensor.set_auto_exposure(False, exposure_us=20000)

pan_SMC = SMC(5, 50, 50, 3)

DISABLE = 1
ENABLE = 0

sq = Pin('P7', Pin.OUT_PP)
ENB = Pin('P3', Pin.OUT_PP)
DIR = Pin('P2', Pin.OUT_PP)

ENB.value(DISABLE)

tim = Timer(4, freq=500)
ch = tim.channel(1, Timer.PWM, pin=sq, pulse_width_percent=50)

RECT_THRESHOLD    = 12000
INIT_FRAMES       = 3
TRACK_DIST_SQR    = 30**2
LOSE_RESET_FRAMES = 5
DEADZONE          = 5

centerx = 80
# centery = 60

CW = 0
CCW = 1

history   = []
confirmed = None
conf_cnt  = 0
lose_cnt  = 0
limmit = DISABLE

clock = time.clock()
while True:
    clock.tick()
    img = sensor.snapshot()

    rects = img.find_rects(threshold = RECT_THRESHOLD)
    if rects:
        lose_cnt = 0
        r = rects[0]
        x,y,w,h = r.rect()
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
        lose_cnt += 1
        if lose_cnt >= LOSE_RESET_FRAMES:
            confirmed = None
            history.clear()
            conf_cnt = 0
            lose_cnt = 0

    if confirmed:
        cx, cy = confirmed
        img.draw_rectangle((cx - w//2, cy - h//2, w, h))
        img.draw_cross(cx, cy)
        # print("Center:", cx, cy)

        if abs(cx - centerx) >= DEADZONE:
            ENB.value(ENABLE)
            pan_SMC.sliding_mode_init(cx, centerx)
            pan_SMC.sliding_mode_control_law()
            pan_U_abs, pan_U_sign = pan_SMC.get_control_input()
            tim.freq(pan_U_abs)  # 仅更新频率，避免重新创建 Timer
            DIR.value(pan_U_sign)
        else:
            ENB.value(DISABLE)
    # 可选：打印当前帧率，监测性能
    # print("FPS:", clock.fps())
