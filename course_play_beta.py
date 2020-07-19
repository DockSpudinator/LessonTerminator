#!/usr/local/bin/python3
# -*- coding:utf-8 -*-
import logging
import os
import re
import time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

# 创建一个日志器，方便后期调试
logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(processName)s-%(funcName)s-%(message)s')
logger = logging.getLogger(__name__)

# 指定chromedriver脚本文件路径
chrome_driver_path = '/Users/llb/software/Chrome/chromedriver/chromedriver'
# 配置到环境变量中
os.environ["webdriver.Chrome.driver"] = chrome_driver_path

# 读取配置文件
options = webdriver.ChromeOptions()
# 添加获取摄像头权限
prefs = {'profile.default_content_setting_values.media_stream_camera': 1}
options.add_experimental_option('prefs', prefs)
# 启动chrom时指定脚本驱动和配置文件
driver = webdriver.Chrome(executable_path=chrome_driver_path, options=options)


# 定义全局播放状态变量
# play_status = 0

# 登录
def login(username, password):
    try:
        driver.get('https://www.bjjnts.cn/login')
        time.sleep(2)
        # 用户名输入框
        username_input = driver.find_element_by_name('username')
        # 密码输入框
        password_input = driver.find_element_by_name('password')

        username_input.send_keys(username)
        password_input.send_keys(password)
        login_button = driver.find_element_by_xpath('//*[@id="formLogin"]/button')
        # 通过键盘点击Enter进行登录
        # login_button.send_keys(Keys.RETURN)
        login_button.click()
        return True
    except:
        return False


# 获取当前课程的所有章节播放列表
def get_course_url_list(first_chapter_url):
    # print(driver.current_url)
    driver.get(first_chapter_url)
    course_ul = driver.find_element_by_xpath('/html/body/div[3]/div/div/div/div[1]/div[2]/ul')
    course_ul_lis = course_ul.find_elements_by_tag_name('li')
    print(len(course_ul_lis))
    course_url_list = list()
    for li in course_ul_lis:
        ele_a = li.find_element_by_class_name('change_chapter')
        course_url_list.append(ele_a.get_attribute('href'))
    return course_url_list


# 播放课程
def play_course(course_url_list):
    try:
        current_url = driver.current_url
        logger.info("当前地址: {0}".format(current_url))
        last_course_url = course_url_list[len(course_url_list) - 1]
        logger.info("最后一个地址: {0}".format(last_course_url))
        play_status = 0
        position = 1
        while current_url != last_course_url:
            while play_end(position):
                play_status = 0
                next_course_url = get_next_course_url(course_url_list)
                driver.get(next_course_url)
                position += 1
                current_url = next_course_url
                # play_course(next_course_url, course_url_list, len(course_url_list))
            else:
                if play_status == 0:
                    play_video()
                    play_status = 1
            time.sleep(5)
    except Exception as e:
        logger.info("异常信息：{0}".format(e))
        driver.quit()


# 播放视频
def play_video():
    video_ele = WebDriverWait(driver, 5).until(lambda d: d.find_element_by_id('studymovie'))
    # 播放视频并进行人脸识别
    if driver.execute_script('return arguments[0].paused', video_ele):
        video_ele.click()
    # 执行js脚本（开启加速播放及静音）
    play_speed_js = 'document.querySelector("video").playbackRate = 4;' \
                    'document.getElementById("studymovie").volume = 0;'
    driver.execute_script(play_speed_js)


# 判断视频是否播放完毕
def play_end(position):
    try:
        video = driver.find_element_by_id('studymovie')
        current_time = driver.execute_script('return arguments[0].currentTime', video)
        total_time = driver.execute_script('return arguments[0].duration', video)
        print(f"当前进度：{current_time}", f"总进度: {total_time}")
        # logger.info("当前地址:{0}.".format(driver.current_url))
        # 刷新当前页面
        # driver.refresh()
        play_progress = driver.find_element_by_xpath(
            f'/html/body/div[3]/div/div/div/div[1]/div[2]/ul/li[{position}]/div/a/span')
        progress_text = play_progress.text.strip()
        print(progress_text)
        reg_result = re.findall(r'\d+%$', progress_text)
        result = reg_result.pop()
        return ('100%'.__eq__(result)) or (current_time == total_time)
    except Exception as e:
        logger.info("错误信息:", e)
        return False


# 获取下一章节播放地址
def get_next_course_url(url_list):
    if len(url_list) <= 0:
        return 0
    current_course_url = driver.current_url
    next_url = ""
    for index, value in enumerate(url_list):
        if current_course_url.strip() == value.strip() and index < len(url_list) - 1:
            next_url = url_list.__getitem__(index + 1)
            print("当前播放地址: " + next_url)
    return next_url


# 获取每个课程的默认首章节url
def get_user_course_list(course_url, lesson_url_prefix):
    if course_url == "":
        return ""
    driver.get(course_url)
    user_course_ul = driver.find_element_by_xpath('/html/body/div[3]/div/div[2]/div/ul')
    user_course_lis = user_course_ul.find_elements_by_tag_name('li')
    user_current_url = list()
    if len(user_course_lis) > 0:
        for li in user_course_lis:
            a_tag = li.find_element_by_xpath('./div[@class="user_coursepic"]/a')
            data_id = a_tag.get_attribute('data-id')
            data_cid = a_tag.get_attribute('data-cid')
            lesson_url = lesson_url_prefix + '/' + data_id + '/' + data_cid
            # print(lesson_url)
            user_current_url.append(lesson_url)
    return user_current_url


if __name__ == '__main__':
    username = '410803199609030024'
    password = '1122333.'
    while username == '':
        username = input("请输入您的用户名：")
        if username == '':
            print("用户名不能为空！")
    while password == '':
        password = input("请输入您的密码：")
        if password == '':
            print("密码不能为空！")
    login_success = login(username, password)
    user_course_url = 'https://www.bjjnts.cn/userCourse'
    user_lesson_study_prefix = 'https://www.bjjnts.cn/lessonStudy'
    if login_success:
        time.sleep(5)
        print("登录成功！")
        # 获取https://www.bjjnts.cn/userCourse页面下所有课程的第一章节列表
        user_current_url_list = get_user_course_list(user_course_url, user_lesson_study_prefix)
        if len(user_current_url_list) > 0:
            # 每个课程的第一章节
            for url in user_current_url_list:
                # 课程的所有章节
                chapter_list_url = get_course_url_list(url)
                play_course(chapter_list_url)
        else:
            driver.quit()
