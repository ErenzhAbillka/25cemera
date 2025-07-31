class SMC:
    def __init__(self, Lambda=1.0, K=1.0, Phi=0.1, time=1):
        self._Lambda = float(Lambda)    # 滑模面斜率常数
        self._K = float(K)              # 控制增益常数
        self._Phi = float(Phi)          # 饱和函数参数
        self._previous_error = 0        # 上一次的误差
        self._time_interval = float(time)  # 时间误差间隔
        self._S = 0                     # 滑模面状态
        self._U = 0                     # 控制输入
        self._error = 0                 # 当前误差

    def diff(self, current_error):
        derivative = (current_error - self._previous_error) / self._time_interval
        self._previous_error = current_error
        return derivative

    def sliding_mode_init(self, laser1, laser2):
        self._error = laser1 - laser2
        error_diff = self.diff(self._error)
        self._S = error_diff + self._Lambda * self._error

        print(f"error: {self._error}, error_diff: {error_diff}, S: {self._S}")

    def sliding_mode_control_law(self):
        """
        动态调整死区范围（适当增大范围以减少抖振）
        """
        base_dead_zone = 6  # 基础死区范围，适当增大到 6
        scaling_factor = 0.15  # 动态调整系数，适当增大到 0.15

        # 计算动态死区范围
        dynamic_dead_zone = base_dead_zone + scaling_factor * abs(self._error)

        if abs(self._error) < dynamic_dead_zone:
            self._U = 0  # 在死区范围内停止控制
        else:
            # 指数趋近律
            adaptive_K = self._K * (1 + 0.5 * abs(self._error) / (1 + abs(self._error)))
            self._U = -adaptive_K * self.sat(self._S)

        print(f"U: {self._U}, sat(S): {self.sat(self._S)}, S: {self._S}, Dead Zone: {dynamic_dead_zone}")

    def sgn(self, value):
        if value > 0:
            return 1
        elif value < 0:
            return -1
        else:
            return 0

    def sat(self, s):
        if abs(s) < self._Phi:
            return s / self._Phi
        else:
            return self.sgn(s) * (1 - 0.1 / abs(s))

    def get_control_input(self):
        U_abs = self.clamp(abs(self._U), 0, 255)
        U_sign = -1 if self._U < 0 else 1
        return int(U_abs), U_sign

    @staticmethod
    def clamp(value, min_val, max_val):
        return max(min_val, min(value, max_val))
