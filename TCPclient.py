import socket
import struct
import re
import random
import sys
from pathlib import Path

class TCPClient:
    def __init__(self):  # 初始化各种属性
        self.server_ip = None
        self.server_port = None
        self.min_chunk_size = 0
        self.max_chunk_size = 0
        self.input_file = None
        self.output_file = None
        self.socket = None
        self.file_content = ""
        self.chunks = []  # 块列表
        self.reversed_chunks = []

    def get_user_input(self):  # 获取用户输入
        try:
            self.server_ip = input("请输入服务器的IP地址：").strip()
            self.server_port = int(input("请输入服务器的端口号 (1024-65535): "))
            self.min_chunk_size = int(input("请输入最小分块大小 (0-1000): "))
            self.max_chunk_size = int(input("请输入最大分块大小 (1-1000): "))
            self.input_file = r"D:\coding\jiwang\task1\test.txt"
            print(f"文件路径为：{self.input_file}")
            self._validate_inputs()
        except ValueError as ve:
            print(f"输入错误：{ve}")
            sys.exit(1)

    def _validate_inputs(self):  # 验证用户输入参数
        if not (1024 <= self.server_port <= 65535):
            raise ValueError("端口号必须在1024到65535之间")
        if self.min_chunk_size < 0:
            raise ValueError("最小分块大小不能小于0")
        if self.max_chunk_size > 1000:
            raise ValueError("最大分块大小不能大于1000")
        if self.min_chunk_size > self.max_chunk_size:
            raise ValueError("最小分块大小不能大于最大分块大小")
        ip_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(ip_pattern, self.server_ip):
            raise ValueError("无效的IP地址格式")

    def read_input_file(self):  # 读取文件内容
        try:
            file_path = Path(self.input_file)
            if not file_path.exists():
                raise FileExistsError(f"文件不存在：{self.input_file}")
            if not file_path.is_file():
                raise ValueError(f"不是有效文件：{self.input_file}")
            with open(file_path, 'r') as f:
                self.file_content = f.read()
            print(f"成功读取文件：{self.input_file}")
            print(f"文件大小{len(self.file_content)}字符")
        except Exception as e:
            print(f"读取文件失败：{e}")
            sys.exit(1)

    def split_into_chunks(self):
        total_size = len(self.file_content)
        current_pos = 0
        while current_pos < total_size:  # 计算当前块大小（随机值，但不超过剩余内容长度）
            chunk_size = min(  # 显示最小值
                random.randint(self.min_chunk_size, self.max_chunk_size),
                total_size - current_pos  # 隐式创建元组
            )
            # 提取块的子序列
            self.chunks.append(self.file_content[current_pos:current_pos + chunk_size])
            current_pos += chunk_size  # 更新索引
        print(f"数据分块完成，共生成{len(self.chunks)}个块")

    def connect_to_server(self):  # 建立与服务器的TCP链接
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建基于TCP协议的套接字ipv4
            self.socket.settimeout(10)  # 设置超时时间为十秒
            self.socket.connect((self.server_ip, self.server_port))  # 绑定ip地址和端口号
            print(f"成功连接到服务器{self.server_ip}:{self.server_port}")
        except (socket.error, OSError) as se:
            print(f"连接服务器失败: {se}")
            sys.exit(1)

    def send_initialization_packet(self):  # 发送初始化包并接收服务器同意包
        try:
            packet = struct.pack('>HI', 1, len(self.chunks))  # 数据打包与解包格式的字符串,类型，长度
            self.socket.sendall(packet)
            print("发送初始化包")
            response = self._receive_packet(expected_type=2, expected_length=0)
            print("接收到服务器同意包")
        except Exception as e:
            print(f"初始化通信失败：{e}")
            self.close_connection()
            sys.exit(1)

    def process_chunks(self):  # 处理所有数据块，发送请求并且反转结果
        try:
            for i, chunk in enumerate(self.chunks, 1):  # enumerate函数会生成索引
                chunk_data = chunk.encode('ascii')  # 发送反转请求包
                packet = struct.pack('>HI', 3, len(chunk_data)) + chunk_data# >大端序 H无符号4字节 I无符号短2字节
                self.socket.sendall(packet)
                # 接受反转结果
                reversed_data = self._receive_packet(expected_type=4)
                self.reversed_chunks.append(reversed_data)
                print(f"第 {i} 块处理完成: {reversed_data}")
        except Exception as e:
            print(f"处理数据块时出错：{e}")
            self.close_connection()
            sys.exit(1)

    # 接受并解析数据包
    def _receive_packet(self, expected_type=None, expected_length=None):
        header = self._receive_exact(6)  # 接收头部六个字节的内容 两字节类型 四字节数据
        packet_type, packet_length = struct.unpack('>HI', header)
        if expected_type is not None and packet_type != expected_type:
            raise ValueError(f"期望包类型 {expected_type}，但收到 {packet_type}")
        data = self._receive_exact(packet_length)  # 接收数据部分
        if expected_length is not None and packet_length != expected_length:
            raise ValueError(f"期望数据长度 {expected_length}，但收到 {packet_length}")
        return data.decode('ascii') if packet_length > 0 else ''  # false返回空字符串 true的话把data按照ascii解码

    def _receive_exact(self, length):  # 接受精确长度的数据
        data = bytearray()  # 可变字节数组对象
        while len(data) < length:
            chunk = self.socket.recv(length - len(data))  # 从套接字接收数据
            if not chunk:
                raise EOFError("连接意外关闭")
            data.extend(chunk)  # 添加到对象末尾
        return bytes(data)

    def generate_output_file(self):  # 生成反转文件
        try:
            reversed_order_chunks = self.reversed_chunks[::-1]
            self.output_file = r"D:\coding\jiwang\task1\reversed_test.txt"
            with open(self.output_file, 'w') as f:
                f.write(''.join(reversed_order_chunks))
            print(f"最终反转文件已保存至: {self.output_file}")
        except Exception as e:
            print(f"生成输出文件失败: {e}")

    def close_connection(self):  # 关闭TCP连接
        if self.socket:
            try:
                self.socket.close()
                print("TCP连接已经关闭")
            except Exception:
                print("TCP连接关闭失败")


def main():
    print("==== TCP客户端启动 ====")
    client = TCPClient()
    try:
        client.get_user_input()
        client.read_input_file()
        client.split_into_chunks()

        print("\n==== 开始数据传输 ====")
        client.connect_to_server()
        client.send_initialization_packet()  # 发送初始化数据包
        client.process_chunks()

        print("\n==== 处理完成 ====")
        client.generate_output_file()

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    finally:
        client.close_connection()
        print("==== 程序已退出 ====")


if __name__ == "__main__":
    main()