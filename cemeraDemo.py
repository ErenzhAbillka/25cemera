import sensor, image, time

# ------------------------
# 摄像头 + 模板加载
# ------------------------
sensor.reset()
sensor.set_pixformat(sensor.RGB565)      # 彩色输出，好画红点
sensor.set_framesize(sensor.QQVGA)       # 160×120，加速处理
sensor.skip_frames(time = 2000)          # 等待自动参数稳定
sensor.set_auto_gain(False)              # 关自动增益
sensor.set_auto_whitebal(False)          # 关自动白平衡
sensor.set_auto_exposure(False, exposure_us=20000)  # 固定曝光

# 加载你保存的模板
tpl = image.Image("/template.png")       # 文件名要和你保存在 SD 卡上的一致

# 模板匹配参数
THRESH = 0.70               # 阈值从 0.5～0.8 之间调整
STEP   = 4                  # 搜索步长，越大越快但精度略差
SEARCH = image.SEARCH_EX    # 快速外插法

clock = time.clock()

while True:
    clock.tick()
    img = sensor.snapshot()  # 彩色帧，方便可视化

    # 执行模板匹配
    match = img.find_template(tpl, THRESH, step=STEP, search=SEARCH)
    if match:
        # 如果返回的是列表，就取第一个(match[0])；否则它就是单个 tuple
        if isinstance(match, list):
            match = match[0]
        mx, my, mw, mh = match

        # 计算矩形中心
        cx = mx + mw // 2
        cy = my + mh // 2

        # 在原图上画红十字和红圈
        img.draw_cross(cx, cy, color=(255, 0, 0), size=15)
        img.draw_circle(cx, cy,  8,   (255, 0, 0))

        print("FPS:%.1f  中心:(%d,%d)" % (clock.fps(), cx, cy))
    else:
        print("FPS:%.1f  未匹配到矩形" % clock.fps())
