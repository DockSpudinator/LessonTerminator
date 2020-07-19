#!/usr/local/bin/python3
# -*- coding:utf-8 -*-
import logging
import os
import re
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# 创建一个日志器，方便后期调试
logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(processName)s-%(funcName)s-%(message)s')
logger = logging.getLogger(__name__)


class CoursePlay():
    # 初始化
    def __init__(self):
        self.user_course_url = 'https://www.bjjnts.cn/userCourse'
        self.user_lesson_study_prefix = 'https://www.bjjnts.cn/lessonStudy'
        # 指定chromedriver脚本文件路径（这里需要下载chromedriver驱动程序）
        self.chrome_driver_path = '/Users/llb/software/Chrome/chromedriver/chromedriver'
        # 配置到环境变量中
        os.environ["webdriver.Chrome.driver"] = self.chrome_driver_path
        # 获取配置文件对象
        self.options = webdriver.ChromeOptions()
        # 添加获取摄像头权限
        self.prefs = {'profile.default_content_setting_values.media_stream_camera': 1}
        self.options.add_experimental_option('prefs', self.prefs)
        # 启动chrom时指定脚本驱动和配置文件
        self.driver = webdriver.Chrome(executable_path=self.chrome_driver_path, options=self.options)

    # 登录
    def user_login(self, username, password):
        try:
            self.driver.get('https://www.bjjnts.cn/login')
            time.sleep(2)
            # 用户名输入框
            username_input = self.driver.find_element_by_name('username')
            # 密码输入框
            password_input = self.driver.find_element_by_name('password')
            # 填充信息到输入框中
            username_input.send_keys(username)
            password_input.send_keys(password)
            # 获取登录按钮
            login_button = self.driver.find_element_by_xpath('//*[@id="formLogin"]/button')
            # 通过键盘点击Enter进行登录
            # login_button.send_keys(Keys.RETURN)
            login_button.click()
            time.sleep(2)
            if self.driver.current_url == 'https://www.bjjnts.cn/userSetting':
                return True
            else:
                return False
        except Exception as e:
            logger.info(e)
            return False

    # 打开新标签
    # def open_new_window(self, cur_url):
    #     # 通过js打开新的标签页
    #     self.driver.execute_script(f'windows.open({cur_url})')
    #     # current_handle = self.driver.current_window_handle
    #     windows_handles = self.driver.window_handles
    #     # print(current_handle, self.driver.current_url)
    #     self.driver.switch_to.window(windows_handles[-1])
    #     print(f"切换到 {self.driver.current_url} 窗口")

    # 判断元素是否存在
    def is_element_exist(self, element, by, value):
        try:
            if not element:
                self.driver.find_element(by=by, value=value)
            else:
                element.find_element(by=by, value=value)
            return True
        except NoSuchElementException as e:
            return False

    # 获取当前课程的所有章节播放列表
    def get_course_url_list(self, first_chapter_url):
        self.driver.get(first_chapter_url)
        course_ul = self.driver.find_element_by_xpath('/html/body/div[3]/div/div/div/div[1]/div[2]/ul')
        course_ul_lis = course_ul.find_elements_by_tag_name('li')
        print(f"共有：{len(course_ul_lis)}章节")
        course_url_list = list()
        for index, li in enumerate(course_ul_lis):
            progressed_text = li.find_element_by_tag_name('span').text
            progress_num = re.findall(r'\d+\.?\d{0,2}', str(progressed_text))
            # lock_flg = self.is_element_exist(li, By.XPATH, './/span/img')
            ele_a = li.find_element_by_xpath('./div/a')
            # 获取data-lock属性
            lock_flg = int(str(ele_a.get_attribute('data-lock')))
            # 如果当前章节观看进度不等于100且存在锁标识，统一添加到集合中
            if progress_num and int(float(progress_num[0])) != 100:
                # 新的实现方式
                course_url_list.append(li)
            if lock_flg == 1:  # data-lock值为,添加到集合中
                course_url_list.append(str(ele_a.get_attribute('class')))
        return course_url_list

    # 播放视频
    def play_video(self, chapter_li):
        try:
            menu_title = chapter_li.find_element_by_class_name('course_study_menutitle').text
            logger.info(f'当前播放章节:{menu_title}')
            video_ele = WebDriverWait(self.driver, 3).until(lambda d: d.find_element_by_id('studymovie'))

            # 获取当前视频的播放进度百分比
            menu_schedule_text = chapter_li.find_element_by_class_name('course_study_menuschedule').text
            menu_schedule_num = re.findall(r'\d+\.?\d{0,2}', menu_schedule_text)
            current_progress = 0
            if len(menu_schedule_num):
                progress_num = float(menu_schedule_num[0])
                # 获取当前视频的总播放时长
                video_duration = self.driver.execute_script("return arguments[0].duration", video_ele)
                # 计算（当前播放进度*总播放时长）/ 100 = 当前已播放进度
                # 这里减去100为了避免直接跳转后立即出现弹窗，出现未知错误！！！
                current_progress = int((progress_num * video_duration) / 100) - 100
            # if current_progress > 100:
            #     current_progress -= 100
            # 跳转到上次播放位置
            if current_progress > 0:
                self.driver.execute_script(f'arguments[0].currentTime = {current_progress}', video_ele)
                time.sleep(1)
            # 执行js脚本（开启加速播放及静音）
            play_speed_js = 'document.getElementById("studymovie").playbackRate = 4;' \
                            'document.getElementById("studymovie").volume = 0;'
            self.driver.execute_script(play_speed_js)
            if self.driver.execute_script('return arguments[0].paused', video_ele):
                video_ele.click()
        except Exception:
            raise

    # 人脸识别
    def face_recognation(self):
        try:
            face_recogn_is_exist = self.is_element_exist(None, By.CLASS_NAME, 'face_recogn')
            if face_recogn_is_exist:
                face_recogn = self.driver.find_element_by_class_name('face_recogn')
                face_recogn_displayed = face_recogn.value_of_css_property('display')
                if face_recogn_displayed == 'block':
                    while face_recogn.value_of_css_property('display') != 'none':
                        try:
                            face_button_is_enabled = self.is_element_exist(None, By.ID, 'face_startbtn')
                            btn_disabled = self.driver.find_element_by_id('face_startbtn').get_attribute("disabled")
                            if face_button_is_enabled and not btn_disabled:
                                self.driver.find_element_by_id('face_startbtn').click()
                            print("正在进行人脸识别中！请稍等！")
                            time.sleep(2)
                        except Exception:
                            break
                    else:
                        self.driver.execute_script('document.getElementById("studymovie").playbackRate = 4;')
        except Exception as e:
            logger.error(e)
            raise

    # 处理弹窗
    def is_continue_watch(self):
        # is_exist = self.is_element_exist(None, By.XPATH, '//a[text()="确定"]')
        while self.is_element_exist(None, By.CLASS_NAME, 'layui-layer-btn0'):
            print("正在处理弹窗，请耐心等候！")
            try:
                confirm_btn = self.driver.find_element_by_class_name('layui-layer-btn0')
                if not confirm_btn:
                    confirm_btn = self.is_element_exist(None, By.XPATH, '//a[text()="确定"]')
                print(str(confirm_btn.tag_name))
                confirm_btn.click()
            except Exception as e:
                logger.error(e)
                break
            time.sleep(3)

    # 判断视频是否播放完毕
    def is_play_end(self):
        try:
            video = self.driver.find_element_by_id('studymovie')
            equal_times, pre_progress, cur_progress = 0, 0, 0
            play_progress_num = 0
            # 循环等待视频播放完毕
            while int(play_progress_num) != 100:
                # 等待处理弹窗
                self.is_continue_watch()
                # 等待处理面部识别
                self.face_recognation()
                # 获取实时播放进度（百分比）
                play_progress_result = self.driver.execute_script('let current_time = arguments[0].currentTime;\
                                                let total_time = arguments[0].duration;\
                                                let progress_num = (current_time / total_time) * 100; \
                                                return progress_num', video)
                play_progress_num = float(str(play_progress_result))

                cur_progress = int(play_progress_num)
                if cur_progress != pre_progress:
                    pre_progress = cur_progress
                else:
                    equal_times += 1
                if equal_times >= 12:
                    break
                print(f"当前进度：{int(play_progress_num)}%")
                time.sleep(5)
            return True
        except Exception as e:
            logger.error("错误信息:", e)
            return False

    # 获取每个课程的默认首章节url
    def get_user_course_list(self, course_url, lesson_url_prefix):
        if course_url == "":
            return list()
        self.driver.get(course_url)
        user_course_ul = self.driver.find_element_by_xpath('/html/body/div[3]/div/div[2]/div/ul')
        user_course_lis = user_course_ul.find_elements_by_tag_name('li')
        user_current_url = {}
        if len(user_course_lis) > 0:
            for li in user_course_lis:

                # 获取每个课程的完成进度
                progress_text = li.find_element_by_xpath(
                    './div[3]/div/div[3]/span[@class="study_complete_percent"]').text
                if progress_text:
                    progress_num = float(progress_text.rstrip('%'))
                    # 已完成的课程不再获取
                    if progress_num != float('100'):
                        a_tag = li.find_element_by_xpath('./div[@class="user_coursepic"]/a')
                        course_title = li.find_element_by_xpath('./div[2]//h2[@class="user_coursetit"]').text
                        data_id = a_tag.get_attribute('data-id')
                        data_cid = a_tag.get_attribute('data-cid')
                        lesson_url = lesson_url_prefix + '/' + data_id + '/' + data_cid
                        user_current_url[lesson_url] = course_title
        return user_current_url

    # 判断是否有弹窗显示
    @staticmethod
    def has_popups(driver):
        try:
            while True:
                is_present = WebDriverWait(driver, 3).until(
                    driver.find_element(By.XPATH, '//*[text()="确定"]'))
                if is_present:
                    driver.find_element_by_xpath('//*[text()="确定"]').click()
        except NoSuchElementException as e:
            logger.error(e)
            driver.quit()

    # 播放每个章节视频
    def play_chapter(self, chapter_li):
        try:
            # 获取当前li标签的a标签
            chapter_li.find_element_by_tag_name('a').click()
            time.sleep(1)
            self.play_video(chapter_li)
            if self.is_play_end():
                return
            else:
                self.driver.quit()
        except Exception as e:
            logger.error(e)
            return


if __name__ == '__main__':
    username = ''
    password = ''
    while username == '':
        username = input("请输入您的用户名：")
        if username == '':
            print("用户名不能为空！")
    while password == '':
        password = input("请输入您的密码：")
        if password == '':
            print("密码不能为空！")

    cp = CoursePlay()
    login_success = cp.user_login(username, password)
    if login_success:
        time.sleep(2)
        logger.info("登录成功！")
        # 获取https://www.bjjnts.cn/userCourse页面下所有课程的第一章节列表
        user_current_url_list = cp.get_user_course_list(cp.user_course_url, cp.user_lesson_study_prefix)
        if len(user_current_url_list) > 0:
            # 获取所有课程
            for url, title in user_current_url_list.items():
                print(f"当前课程：{title}")
                # 课程的所有章节的a标签
                chapter_list_url = cp.get_course_url_list(url)
                if len(chapter_list_url) <= 0:
                    continue
                for chapter in chapter_list_url:
                    if isinstance(chapter, str):
                        # 根据列表中已存在li元素的class值，重新获取一次li标签
                        new_li = WebDriverWait(cp.driver, 3).until(
                            lambda d: d.find_element_by_xpath(f'//a[@class="{chapter}"]/ancestor::li'))
                        chapter = new_li
                    cp.play_chapter(chapter)
        print("你已完成全部课程！！！")
        cp.driver.quit()
    else:
        logger.error("登录失败！，请重新启动")
        cp.driver.quit()
