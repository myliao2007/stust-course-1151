import myid                      # 身份指紋（在 B 板上跑）
CAP = 2000.0                     # 電池容量 mAh
I_IDLE = None                    # 選填：記錄表第 4 段（連上後閒置）的平均 mA

with open("duty_result.txt") as f:       # 五個數字都是 B 用 INA219 量的
    I_on, t_on, I_slp, t_slp, I_meas = [float(v) for v in f.read().split(",")]

T = t_on + t_slp
duty = t_on / T
I_avg = (I_on * t_on + I_slp * t_slp) / T
hours = CAP / I_avg

print('醒著那段 %.1f mA·秒，睡著那段 %.1f mA·秒' % (I_on * t_on, I_slp * t_slp))
print('Duty Cycle %.2f %%' % (duty * 100))
print('平均電流   %.3f mA' % I_avg)
print('理論續航   %.1f 小時' % hours)
print('保守估計   %.1f 小時' % (hours * 0.7))
diff = (I_avg - I_meas) / I_meas * 100
print('B 直接量   %.3f mA，和公式差 %.1f %%' % (I_meas, diff))
if I_IDLE:                       # 一直連著 vs 睡了再重連
    T_be = t_on * (I_on - I_slp) / (I_IDLE - I_slp)
    print('一直連著 %.1f mA；週期超過 %.1f 秒，睡了再重連比較省' % (I_IDLE, T_be))
