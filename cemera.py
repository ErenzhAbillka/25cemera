import sensor, image, time
from pyb import Timer, Pin
from SMC2 import SMC

# ==================== 摄像头初始化 ====================
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
sensor.set_auto_exposure(False, exposure_us=20000)

# ==================== 滑模控制器初始化 ====================
pan_SMC = SMC(2, 50, 60, 2)

# ==================== 步进电机与定时器引脚 ====================
DISABLE = 1
ENABLE  = 0

sq   = Pin('P7', Pin.OUT_PP)   # 步进脉冲
ENB  = Pin('P2', Pin.OUT_PP)   # 使能
DIR  = Pin('P3', Pin.OUT_PP)   # 方向

# 默认搜索速度
DEFAULT_SPIN_FREQ = 1000

# 初始化为“搜索”模式（CCW）
ENB.value(ENABLE)
DIR.value(1)  # 1 = CCW
tim = Timer(4, freq=DEFAULT_SPIN_FREQ)
ch  = tim.channel(1, Timer.PWM, pin=sq, pulse_width_percent=50)

# ==================== 跟踪参数 ====================
RECT_THRESHOLD    = 12000
INIT_FRAMES       = 3
TRACK_DIST_SQR    = 30**2
LOSE_RESET_FRAMES = 5
DEADZONE          = 1     # 停机阈值 <1px
PURE_FREQ_THRESH  = 5     # SMC 启动阈值 >5px
CENTERX           = 60    # 旋转后图像中心 x

# 状态变量
history         = []
confirmed       = None
conf_cnt        = 0
lose_cnt        = 0
last_error_sign = 1       # 上一次误差符号

clock = time.clock()

while True:
    clock.tick()
    img = sensor.snapshot()

    # —— 矩形检测 + A4 比例过滤 —— #
    rects = []
    for r in img.find_rects(threshold=RECT_THRESHOLD):
        x, y, w, h = r.rect()
        aspect = (w/h if w>h else h/w)
        if 1.25 < aspect < 1.55:
            rects.append(r)

    if rects:
        lose_cnt = 0
        r = rects[0]
        x, y, w, h = r.rect()
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

    # —— 搜索模式 —— #
    if confirmed is None:
        ENB.value(ENABLE)
        DIR.value(1 - last_error_sign)
        tim.freq(DEFAULT_SPIN_FREQ)
        continue

    # —— 跟踪模式 —— #
    cx, cy = confirmed
    img.draw_rectangle((cx - w//2, cy - h//2, w, h))
    img.draw_cross(cx, cy)

    pan_error = cy - CENTERX
    last_error_sign = 1 if pan_error >= 0 else 0

    # ===== 死区逻辑（倒序：SMC→频率→停机） =====
    if abs(pan_error) > PURE_FREQ_THRESH:
        # 误差大于5px → 用 SMC
        ENB.value(ENABLE)
        pan_SMC.sliding_mode_init(cy, CENTERX)
        pan_SMC.sliding_mode_control_law()
        pan_U_abs, pan_U_sign = pan_SMC.get_control_input()
        tim.freq(1 + pan_U_abs * 8)
        DIR.value(pan_U_sign)
        print("SMC")

    elif abs(pan_error) > DEADZONE:
        # 误差在(1,5]px → 直接用频率消除误差
        ENB.value(ENABLE)
        DIR.value(0 if pan_error >= 0 else 1)
        tim.freq(300)
        print("freq")

    else:
        # 误差 ≤1px → 停机
        ENB.value(0)
        tim.freq(1)
        print("stop")
    # ===== 死区逻辑结束 =====

    print(f"error: {pan_error}")

    # （可选）打印帧率
    # print("FPS:", clock.fps())
