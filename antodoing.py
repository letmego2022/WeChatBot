
from PIL import ImageGrab
import os
import base64
from openai import OpenAI
import pyautogui
import pyperclip
import time

def move_and_click(x, y):
    """
    鼠标移动到指定坐标并执行鼠标左键点击
    :param x: 目标位置的 x 坐标
    :param y: 目标位置的 y 坐标
    """
    try:
        # 移动鼠标到指定位置
        pyautogui.moveTo(x, y, duration=0.5)  # duration 参数控制移动速度
        # 执行鼠标左键点击
        pyautogui.click()
        print(f"鼠标已移动到 ({x}, {y}) 并执行了左键点击")
    except Exception as e:
        # 捕获异常并打印错误信息
        print(f"移动鼠标或点击时发生错误：{str(e)}")

def recognize_image_and_respond(yaoqiu):
    """
    上传图片并根据要求生成回答
    :param image_path: 图片文件的路径
    :param api_key: OpenAI API 密钥
    :param base_url: OpenAI API 的基础 URL
    :param yaoqiu: 对图片识别的要求
    :return: 回答内容
    """
    image_path="screenshot.png"
    api_key="sk-3---------------------"
    base_url="https://api.moonshot.cn/v1"
    try:
        # 初始化 OpenAI 客户端
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        
        # 读取图片文件并编码为 base64
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        image_url = f"data:image/{os.path.splitext(image_path)[1]};base64,{base64.b64encode(image_data).decode('utf-8')}"
        systeminfo = '''【角色设定】
你是一名专业的微信对话处理助手，具备精准的场景判断和自然语言理解能力。
【任务流程】
场景判断
分析对话上下文特征（如多人发言、@提醒、群公告等）
确认为群聊场景时，立即终止处理，仅回复："群聊"
私聊处理
a. 意图解析
识别用户的核心需求（咨询/闲聊/求助等）
辨别潜在的情感倾向（紧急/愉悦/焦虑等）
b. 应答生成
提供准确、简洁、友善的解决方案
融入自然的口语化表达，避免机械感
严格使用指定格式：
Lewis的私人AI助理[^_^]:〈ANSWER〉
【输出规则】
禁止自我身份声明
禁用Markdown格式
单次回复不超过200字
中文口语化表达，必要时使用表情符号
群聊判断需达到100%确信度

【异常处理】
遇到无法识别的外语消息，回复："喵~ 检测到外星语啦！"
收到文件/图片时，回复："已收到文件，正在启动智能解析..."'''
        # 构造请求内容
        completion = client.chat.completions.create(
            model="moonshot-v1-32k-vision-preview",
            messages=[
                {"role": "system", "content": systeminfo},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                        {
                            "type": "text",
                            "text": yaoqiu,
                        },
                    ],
                },
            ],
        )
        
        # 返回回答内容
        return completion.choices[0].message.content
    
    except Exception as e:
        # 捕获异常并返回错误信息
        error_message = f"处理图片时发生错误：{str(e)}"
        return error_message


def capture_rectangle():
    """
    截取指定位置的矩形区域截图
    :param x: 矩形左上角的 x 坐标
    :param y: 矩形左上角的 y 坐标
    :param width: 矩形的宽度
    :param height: 矩形的高度
    :return: PIL.Image 对象
    """
    x=461
    y=28
    width=590
    height=860
    # 定义矩形区域的边界框（bbox）
    bbox = (x, y, x + width, y + height)
    
    # 截取指定区域的图像
    screenshot = ImageGrab.grab(bbox=bbox)
    time.sleep(0.5)
    # 保存截图到文件（可选）
    screenshot.save("screenshot.png")
    print("截图已完成")
    # 返回截图对象
    return screenshot


def is_red_color(color):
    # 定义红色的范围（可以根据需要调整）
    red_threshold = 150  # 红色分量的最小值
    green_threshold = 100  # 绿色分量的最大值
    blue_threshold = 100  # 蓝色分量的最大值
    
    red, green, blue = color
    if red >= red_threshold and green <= green_threshold and blue <= blue_threshold:
        return True
    return False

def is_green_color(color):
    """
    判断颜色是否为绿色
    :param color: 一个包含 (red, green, blue) 分量的元组
    :return: 如果颜色属于绿色范围，返回 True；否则返回 False
    """
    # 定义绿色的范围（可以根据需要调整）
    green_threshold = 150  # 绿色分量的最小值
    red_threshold = 100    # 红色分量的最大值
    blue_threshold = 100   # 蓝色分量的最大值
    
    red, green, blue = color
    if green >= green_threshold and red <= red_threshold and blue <= blue_threshold:
        return True
    return False

def get_pixel_color_at_position(x, y):
    # 截取指定位置的一个像素点
    bbox = (x, y, x + 1, y + 1)  # 定义一个1x1像素的区域
    img = ImageGrab.grab(bbox)  # 截取该区域的图像
    
    # 获取该像素点的颜色
    pixel_color = img.getpixel((0, 0))

    # 判断是否为红色
    if is_red_color(pixel_color):
        print("该颜色属于红色")
        return True
    else:
        print("该颜色不属于红色")
        return False

def Is_a_dialogue(x, y):
    # 截取指定位置的一个像素点
    bbox = (x, y, x + 1, y + 1)  # 定义一个1x1像素的区域
    img = ImageGrab.grab(bbox)  # 截取该区域的图像
    
    # 获取该像素点的颜色
    pixel_color = img.getpixel((0, 0))

    # 判断是否为红色
    if is_green_color(pixel_color):
        print("该颜色属于绿色")
        return True
    else:
        print("该颜色不属于绿色")
        return False



def send_message_at_position(x, y, message, duration=0.5):
    """
    鼠标移动到指定坐标，左键点击，写入内容，然后回车发送
    :param x: 目标位置的 x 坐标
    :param y: 目标位置的 y 坐标
    :param message: 要写入的内容
    :param duration: 鼠标移动的持续时间（秒，默认 0.5 秒）
    """
    try:
        # 移动鼠标到指定位置
        pyautogui.moveTo(x, y, duration=duration)
        # 执行鼠标左键点击
        pyautogui.click()
        # 等待 0.5 秒，确保点击操作完成
        time.sleep(0.5)
        
        # 将消息复制到剪贴板
        pyperclip.copy(message)
        # 模拟粘贴操作
        pyautogui.hotkey('ctrl', 'v')
        # 等待 0.5 秒，确保粘贴操作完成
        time.sleep(0.5)
        
        # 按下回车键发送
        pyautogui.press('enter')
        print(f"已发送消息：'{message}' 到位置 ({x}, {y})")
    except Exception as e:
        # 捕获异常并打印错误信息
        print(f"发送消息时发生错误：{str(e)}")

def handle_dialog(x, y, yaoqiu):
    """
    处理单个对话框的逻辑
    :param x: 对话框的 x 坐标
    :param y: 对话框的 y 坐标
    :param yaoqiu: 对图片识别的要求
    """
    if get_pixel_color_at_position(x, y):
        # 点击进入对话框
        move_and_click(x, y)
        time.sleep(0.5)  # 等待点击操作完成
        # 判断是否为对话框
        if Is_a_dialogue(903, 957):
            # 截图
            capture_rectangle()
            # 识别图片内容
            response = recognize_image_and_respond(yaoqiu)
            print(response)
            # 判断是否为群聊
            if "群聊" not in response:
                # 发送消息
                send_message_at_position(510, 875, response)

def run_periodically(x, y, interval=15):
    """
    每隔指定的时间间隔运行一次 get_pixel_color_at_position 函数
    :param x: 指定位置的 x 坐标
    :param y: 指定位置的 y 坐标
    :param interval: 时间间隔（秒）
    """
    yaoqiu = '''首先识别聊天对话类型，如果群聊仅需回复:群聊。
若是两人正常对话，首先理解对方的对话意图，并给出合适的回答。仅需回复回复内容，回复内容的格式为：Lewis的私人AI助理[^_^]:{此处填写回答内容}'''

    while True:
        for offset in [0, 99, 99*2]:
            handle_dialog(x, y + offset, yaoqiu)
        time.sleep(interval)

# 示例：每隔15秒运行一次
x1 = 159  # 指定的 x 坐标
y1 = 111  # 指定的 y 坐标
run_periodically(x1, y1, interval=60)
