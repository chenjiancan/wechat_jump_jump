import os
import cv2
import numpy as np
import time
import random
import subprocess

# 使用的Python库及对应版本：
# python 3.6
# opencv-python 3.3.0
# numpy 1.13.3
# 用到了opencv库中的模板匹配和边缘检测功能

adb = "adb -s 1db61630 "


def get_screenshot(id):
    # os.system(adb + 'shell screencap -p /sdcard/%s.png' % str(id))
    # os.system(adb + 'pull /sdcard/%s.png .' % str(id))
    # os.system(adb + 'shell rm /sdcard/%s.png .' % str(id))  ## delete
    screenshot_way = 2
    if screenshot_way == 2 or screenshot_way == 1:
        process = subprocess.Popen(adb + 'shell screencap -p', shell=True, stdout=subprocess.PIPE)
        screenshot = process.stdout.read()
        if screenshot_way == 2:
            binary_screenshot = screenshot.replace(b'\r\n', b'\n')
        else:
            binary_screenshot = screenshot.replace(b'\r\r\n', b'\n')
        f = open('%s.png' % (str(id),), 'wb')
        f.write(binary_screenshot)
        f.close()
    elif screenshot_way == 0:
        os.system(adb + 'shell screencap -p /sdcard/%s.png' % str(id))
        os.system(adb + 'pull /sdcard/%s.png .' % str(id))
        os.system(adb + 'shell rm /sdcard/%s.png .' % str(id))  ## delete


def jump(distance):
    # 这个参数还需要针对屏幕分辨率进行优化
    press_time = int(distance * 1.39)   # 1.35  对小米6 1.40 更准，1.35 会出现跳不到

    # x, y = 320, 410
    x, y = 300, 500
    x += random.randrange(-20, 20)
    y += random.randrange(-30, 30)
    cmd = adb + 'shell input swipe {x} {y} {x} {y}  {t}'.format(x=x, y=y, t=press_time)
    os.system(cmd)


def get_center(img_canny, ):
    # 利用边缘检测的结果寻找物块的上沿和下沿
    # 进而计算物块的中心点
    y_top = np.nonzero([max(row) for row in img_canny[400:]])[0][0] + 400
    x_top = int(np.mean(np.nonzero(canny_img[y_top])))

    y_bottom = y_top + 50
    for row in range(y_bottom, H):
        if canny_img[row, x_top] != 0:
            y_bottom = row
            break

    x_center, y_center = x_top, (y_top + y_bottom) // 2
    return img_canny, x_center, y_center


# # 第一次跳跃的距离是固定的
# jump(530)
# time.sleep(1)

# 匹配小跳棋的模板
temp1 = cv2.imread('temp_player.jpg', cv2.IMREAD_GRAYSCALE)
w1, h1 = temp1.shape[1], temp1.shape[0]

# 匹配游戏结束画面的模板
temp_end = cv2.imread('temp_end.jpg', cv2.IMREAD_GRAYSCALE)

# 匹配中心小圆点的模板
temp_white_circle = cv2.imread('temp_white_circle.jpg', cv2.IMREAD_GRAYSCALE)
w2, h2 = temp_white_circle.shape[1], temp_white_circle.shape[0]

jump_count = 0
img_rgb = None
# 循环直到游戏失败结束
for i in range(300):

    get_screenshot(0)
    img_gray = cv2.imread('%s.png' % 0, cv2.IMREAD_GRAYSCALE)
    img_rgb = cv2.imread('%s.png' % 0, cv2.IMREAD_ANYCOLOR)
    # from shutil import copyfile
    # copyfile('%s.png' % 0, '%s_copy.png' % 0)

    # 如果在游戏截图中匹配到带"再玩一局"字样的模板，则循环中止
    res_end = cv2.matchTemplate(img_gray, temp_end, cv2.TM_CCOEFF_NORMED)
    if cv2.minMaxLoc(res_end)[1] > 0.95:
        print('Game over! {}'.format(jump_count))
        jump_count = 0
        break

    # 模板匹配截图中小跳棋的位置
    res1 = cv2.matchTemplate(img_gray, temp1, cv2.TM_CCOEFF_NORMED)
    min_val1, max_val1, min_loc1, max_loc1 = cv2.minMaxLoc(res1)

    cv2.rectangle(img_rgb, (max_loc1[0], max_loc1[1]), (max_loc1[0] + w1, max_loc1[1] + h1), (0, 255, 0), 3)
    if max_val1 > 0.7:
        center1_loc = (max_loc1[0] + 39, max_loc1[1] + 189)
    else:
        print("cant match bottle! with match_val:{} GameOver!...".format(max_val1))
        break

    # 先尝试匹配截图中的中心原点，
    # 如果匹配值没有达到0.95，则使用边缘检测匹配物块上沿
    res2 = cv2.matchTemplate(img_gray, temp_white_circle, cv2.TM_CCOEFF_NORMED)
    min_val2, max_val2, min_loc2, max_loc2 = cv2.minMaxLoc(res2)

    cv2.rectangle(img_rgb, (max_loc2[0], max_loc2[1]), (max_loc2[0] + w2, max_loc2[1] + h2), (255, 0, 0), 3)
    if max_val2 > 0.90:
        print('found white circle!')
        x_center, y_center = max_loc2[0] + w2 // 2, max_loc2[1] + h2 // 2
    else:
        print('DONT found white circle! with match_val:{}    Try Edge Detect'.format(max_val2))
        # 边缘检测
        img_gray = cv2.GaussianBlur(img_gray, (5, 5), 0)
        canny_img = cv2.Canny(img_gray, 1, 10)
        H, W = canny_img.shape

        # 消去小跳棋轮廓对边缘检测结果的干扰
        for k in range(max_loc1[1] - 10, max_loc1[1] + 189):
            for b in range(max_loc1[0] - 10, max_loc1[0] + 100):
                canny_img[k][b] = 0

        img_gray, x_center, y_center = get_center(canny_img)

        cv2.circle(img_rgb, (x_center, y_center), 10, (0, 0, 255), 3)

    cv2.circle(img_rgb, (center1_loc[0], center1_loc[1]), 10, (0, 255, 255), 2)
    cv2.imwrite('last_rgb.png', img_rgb)
    # 将图片输出以供调试
    img_gray = cv2.circle(img_gray, (x_center, y_center), 10, 255, -1)
    # cv2.rectangle(canny_img, max_loc1, center1_loc, 255, 2)
    cv2.imwrite('last.png', img_gray)

    distance = (center1_loc[0] - x_center) ** 2 + (center1_loc[1] - y_center) ** 2
    distance = distance ** 0.5 + random.randrange(-2, 2)
    jump(distance)

    t = 1.9 + random.randrange(-5, 5) * 0.1
    time.sleep(t)  # 1.3s

    jump_count += 1
    print("after sleep: {t} jumps: {0} distance: {1}  for {2} sec".format(jump_count, distance, int(distance * 1.35),
                                                                          t=t))
