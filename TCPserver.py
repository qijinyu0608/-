import socket
import sys
import threading
import struct#字节数据和原生数据类型（如整数、浮点数）之间的转换
from typing import Tuple

class TCPServer:
    INIT_PACKER=1#初始包
    AGREE_PACKET=2#同意包
    REQUEST_PACKET = 3#请求包
    RESPONSE_PACKET = 4#响应包
    
    def __init__(self,port:int):#port预期是int类型
        self.port=port
        self.server_socket=None
        self.running=False
        self.encoding='utf-8'
    
    def validate_port(self):
        if not (1024 <= self.port <= 65535):
            raise ValueError("端口号必须在1024到65535之间")
        
    def start_server(self):#启动服务器开始监听连接
        try:
            self.server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)#允许地址复用
            self.server_socket.bind(('0.0.0.0',self.port))#0.0.0.0服务器将监听所有可用的网络接口
            self.server_socket.listen(5)#最多可容纳五个请求
            self.running=True
            print(f"服务器启动成功，监听端口 {self.port}...")
            print("等待客户端连接...")
            
        except Exception as e:
            print(f"服务器启动失败: {e}")
            raise
        
    def handle_connections(self):#处理客户端连接的主循环
        try:
            while self.running:
                #分离监听和通信：服务器的监听套接字（self.server_socket）只负责监听客户端的连接请求，
                # 而和客户端的实际通信则通过新创建的 client_socket 来完成。这种分离可以让服务器同时处理多个客户端的连接。
                client_socket,client_address=self.server_socket.accept()#返回元组包括

                client_thread=threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,client_address),
                    daemon=True#设置为守护线程，随着主线程的结束而结束
                )
                client_thread.start()#启动线程
        except KeyboardInterrupt:
            print("\n服务器关闭中...")
        finally:
            self.shutdown()
    #处理单个客户端连接的方法        
    def _handle_client(self,client_socket,client_address):
        print(f"新连接来自 {client_address}")
        try:
            init_packet=self._receive_packet(client_socket,6)
            if not init_packet:
                print(f"来自 {client_address} 的初始化包为空")
                return
            packet_type,chunk_count=struct.unpack('>HI',init_packet)#解包初始化包
            if packet_type!=self.INIT_PACKER:#验证初始化包
                print(f"来自 {client_address} 的无效初始化包(类型: {packet_type})")
                self._send_error_packet(client_socket, "无效的初始化包类型")
                return
            agree_packet=struct.pack('>HI',self.AGREE_PACKET,0)#发送同意包
            client_socket.sendall(agree_packet)
            print(f"已向 {client_address} 发送同意包")
            
            for chunk_idx in range(1,chunk_count+1):
                try:
                    request_header=self._receive_packet(client_socket,6)#接收请求包
                    if not request_header:
                        print(f"来自 {client_address} 的请求包为空 (块 {chunk_idx})")
                        break
                    
                    packet_type,data_length=struct.unpack('>HI',request_header)
                    
                    if packet_type != self.REQUEST_PACKET:#验证请求包
                        print(f"来自 {client_address} 的无效请求包(类型: {packet_type}, 块 {chunk_idx})")
                        self._send_error_packet(client_socket, "无效的请求包类型")
                        break
                    #接收请求数据
                    request_data=self._receive_packet(client_socket,data_length)
                    if not request_data:
                        print(f"来自 {client_address} 的请求数据为空 (块 {chunk_idx})")
                        break
                    #处理数据
                    original_str = request_data.decode(self.encoding)
                    reversed_str = original_str[::-1]
                    reversed_data = reversed_str.encode(self.encoding)
                    #发送响应包
                    response_header=struct.pack('>HI',self.RESPONSE_PACKET,len(reversed_data))
                    client_socket.sendall(response_header+reversed_data)
                    print(f"已向 {client_address} 发送块 {chunk_idx} 反转结果")
                    
                except struct.error as se:
                    print(f"来自 {client_address} 的数据包解析错误 (块 {chunk_idx}): {se}")
                    break
                except UnicodeDecodeError as ude:
                    error_msg = f"编码错误: 无法解码块 {chunk_idx} 中的字符 (位置 {ude.start}-{ude.end})"
                    print(f"来自 {client_address} 的数据: {error_msg}")
                    break
                except Exception as e:
                    print(f"处理块 {chunk_idx} 时出错: {e}")
                    break
        except ConnectionResetError:
            print(f"客户端 {client_address} 重置了连接")
        except Exception as e:
            print(f"处理客户端 {client_address} 时发生未预期错误: {e}")
        finally:
            client_socket.close()
            print(f"连接关闭: {client_address}")  
            
    def _receive_packet(self, sock, size):#精确接收指定大小的数据包
        data = bytearray()
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise ConnectionAbortedError("连接意外关闭")
            data.extend(chunk)
        return bytes(data)
    
    def shutdown(self):
        self.running=False
        if self.server_socket:
            try:
                self.server_socket.close()
                print("服务器关闭")
            except Exception:
                print("服务器无法正常关闭")
                
def main():
    try:
        port = int(input("请输入服务器端口号 (1024-65535): "))# 获取并验证端口号
        # 创建并启动服务器
        server = TCPServer(port)
        server.validate_port()
        server.start_server()
        server.handle_connections()
        
    except ValueError as ve:
        print(f"输入错误: {ve}")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    
          
                    
                        
                        
            