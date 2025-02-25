
from PIL import ImageGrab
import os
import base64
import pyautogui
import pyperclip
import time
from datetime import datetime
import ollama
from openai import OpenAI
from json_repair import repair_json
import re
import json
import time
import sqlite3
import json
from datetime import datetime

DB_NAME = "messages.db"

def create_database():
    """创建SQLite数据库和数据表"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 创建表，message 存储 JSON 格式的字符串
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_records (
        duifangnickname TEXT PRIMARY KEY,
        message TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def insert_or_update_message(json_data):
    """解析 JSON 并去重更新数据库"""
    duifangnickname = json_data.get("duifangnickname")
    new_messages = json_data.get("message", [])

    if not duifangnickname or not new_messages:
        print("无效数据")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 查询当前的 message
    cursor.execute("SELECT message FROM chat_records WHERE duifangnickname = ?", (duifangnickname,))
    row = cursor.fetchone()

    if row:
        # 获取已有消息并转换为列表
        existing_messages = json.loads(row[0]) if row[0] else []

        # 去重（保留原格式，避免同样的 "you"/"me" 结构重复）
        unique_messages = []
        seen = set()
        for msg in existing_messages + new_messages:
            msg_str = json.dumps(msg, ensure_ascii=False)  # 转成字符串以便去重
            if msg_str not in seen:
                seen.add(msg_str)
                unique_messages.append(msg)

        # 更新数据库
        cursor.execute(
            "UPDATE chat_records SET message = ?, updated_at = ? WHERE duifangnickname = ?",
            (json.dumps(unique_messages, ensure_ascii=False), datetime.now(), duifangnickname)
        )
        print(f"更新 {duifangnickname} 的消息")
    else:
        # 不存在，直接插入
        unique_messages = []
        seen = set()
        for msg in new_messages:
            msg_str = json.dumps(msg, ensure_ascii=False)
            if msg_str not in seen:
                seen.add(msg_str)
                unique_messages.append(msg)

        cursor.execute(
            "INSERT INTO chat_records (duifangnickname, message, updated_at) VALUES (?, ?, ?)",
            (duifangnickname, json.dumps(unique_messages, ensure_ascii=False), datetime.now())
        )
        print(f"新增 {duifangnickname} 的消息")

    conn.commit()
    conn.close()


def get_messages_by_nickname(duifangnickname):
    """根据 duifangnickname 读取消息"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT message FROM chat_records WHERE duifangnickname = ?", (duifangnickname,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return json.loads(row[0])  # 解析 JSON 格式的消息
    else:
        return []  # 不存在则返回空列表



def checkjson(one_with_json):
    try:
        if '```' in one_with_json:
            json_string = one_with_json.split('```')[1].strip()[4:].strip()
        else:
            json_string = one_with_json
        repaired_json_string = repair_json(json_string)
        if repaired_json_string:
            context = json.loads(repaired_json_string)
        else:
            context = {}
    except json.JSONDecodeError:
        context = {}
    return context


API_MODEL = 'deepseek-r1'
client = OpenAI(api_key='deepseek-r1', base_url='http://192.168.0.102:11434/v1')


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
    api_key="sk-"
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
        systeminfo = '''
- Role: 数据格式转换专家和JSON架构设计师
- Background: 用户需要将微信聊天截图中的信息提取并转化为特定JSON格式的聊天记录，这种格式包含对方昵称以及分组的聊天对话内容。这可能是为了将聊天记录用于特定的软件应用或数据分析，需要符合特定的数据结构。
- Profile: 你是一位精通数据格式转换和JSON架构设计的专家，擅长从图像中提取文本信息，并将其准确地转换为符合特定需求的结构化数据格式。你对JSON格式有深入的理解，能够确保数据的完整性和准确性。
- Skills: 你具备图像识别技术、文本解析能力、数据结构化处理能力以及对JSON格式的熟练掌握，能够高效地完成从图像到结构化数据的转换。
- Goals: 将微信聊天截图中的对方昵称和聊天对话准确提取，并以用户指定的JSON格式输出，确保数据的完整性和可读性。
- Constrains: 转换过程中必须确保数据的准确性，避免信息丢失或错误。输出的JSON格式应符合用户指定的结构，易于被其他程序读取和处理。
- OutputFormat: JSON格式，包含对方昵称以及分组的聊天对话内容。
- Workflow:
  1. 从微信聊天截图中提取文本信息，包括对方昵称和聊天对话。
  2. 将提取的文本信息进行解析，按照对方昵称和聊天对话的结构进行组织。
  3. 将解析后的信息以用户指定的JSON格式输出，确保格式规范且易于读取。
- Examples:
  - 例子1：
    微信聊天截图内容：
    ```
    对方昵称：小三
    聊天对话：
    小三：你好啊
    我：你好
    小三：今天天气不错
    我：是啊，适合出去玩
    ```
    输出的JSON格式：
    ```json
    {
        "duifangnickname": "小三",
        "message": [
            {"you": "你好啊"},
            {"me": "你好"},
            {"you": "今天天气不错"},
            {"me": "是啊，适合出去玩"}
        ]
    }
    ```
  - 例子2：
    微信聊天截图内容：
    ```
    对方昵称：小四
    聊天对话：
    小四：最近忙不忙
    我：挺忙的，你呢
    小四：我也是，最近项目很多
    ```
    输出的JSON格式：
    ```json
    {
        "duifangnickname": "小四",
        "message": [
            {"you": "最近忙不忙"},
            {"me": "挺忙的，你呢"},
            {"you": "我也是，最近项目很多"}
        ]
    }
    ```
'''
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
                        # {
                        #     "type": "text",
                        #     "text": yaoqiu,
                        # },
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
    x=395
    y=20
    width=570
    height=870
    # 定义矩形区域的边界框（bbox）
    bbox = (x, y, x + width, y + height)
    
    # 截取指定区域的图像
    screenshot = ImageGrab.grab(bbox=bbox)
    time.sleep(0.5)
    # 保存截图到文件（可选）
    screenshot.save("screenshot.png")
    print(">>会话截图已完成")
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
        # print(">来了新信息")
        return True
    else:
        # print(">旧信息")
        return False

def Is_a_dialogue(x, y):
    # 截取指定位置的一个像素点
    bbox = (x, y, x + 1, y + 1)  # 定义一个1x1像素的区域
    img = ImageGrab.grab(bbox)  # 截取该区域的图像
    
    # 获取该像素点的颜色
    pixel_color = img.getpixel((0, 0))

    # 判断是否为红色
    if is_green_color(pixel_color):
        print(">>>确认为聊天框")
        return True
    else:
        print(">>>公众号更新")
        return False

def find_application(image_path):
    """
    根据图片路径查找应用图标并单击打开应用。
    
    参数:
        image_path (str): 图片文件的路径。
    """
    try:
        # 尝试查找图片中心位置
        location = pyautogui.locateCenterOnScreen(image_path)
        
        if location:
            x, y = location
            return True
        else:
            return False
    
    except pyautogui.ImageNotFoundException:
        return False
       
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
        if Is_a_dialogue(838, 980):
            if not find_application('./pic/qunliao.png'):
                # 截图
                capture_rectangle()
                # 识别图片内容
                MAX_RETRIES = 3  # 设置最大重试次数，防止死循环

                res_json = {}
                attempts = 0

                while not res_json and attempts < MAX_RETRIES:
                    res_json = checkjson(recognize_image_and_respond(yaoqiu))
                    attempts += 1

                if not res_json:
                    print("获取 res_json 失败，已达到最大重试次数")
                # else:
                #     print("成功获取 res_json:", res_json)

                try:
                    insert_or_update_message(res_json)
                except:
                    print('error')
                # send_message_at_position(424, 902, response)
            else:
                print(">>>>>>>>>>>群聊--放弃发送内容")
            # send_message_at_position(424, 902, "测试")



def run_periodically(x, y, interval=15):
    """
    每隔指定的时间间隔运行一次 get_pixel_color_at_position 函数
    仅在每天的12:00-13:00和18:00-19:00时间段内运行。
    :param x: 指定位置的 x 坐标
    :param y: 指定位置的 y 坐标
    :param interval: 时间间隔（秒）
    """
    yaoqiu = '''首先识别图片中的聊天对话类型，如果群聊仅需回复:群聊。
若是两人正常对话，首先理解对方的对话意图，并给出合适的回答。仅需回复回复内容，回复内容的格式为：Lewis的AI助理[^_^]:{此处填写回答内容}'''

    while True:
        for offset in [0, 80, 80*2]:
            handle_dialog(x, y + offset, yaoqiu)
        time.sleep(interval)

create_database()
# 示例：每隔15秒运行一次
x1 = 124  # 指定的 x 坐标
y1 = 90   # 指定的 y 坐标
run_periodically(x1, y1, interval=10)

