TCP 客户端 - 服务器文件内容反转项目

项目概述
本项目包含一个 TCP 客户端和一个 TCP 服务器，其主要功能是将客户端指定文件的内容进行分块，发送到服务器，服务器对每个数据块进行反转处理后返回给客户端，最后客户端将反转后的数据块按逆序保存为新文件。

项目结构

TCPclient.py: TCP 客户端代码，负责读取文件、分块、与服务器通信并生成反转后的文件。
TCPserver.py: TCP 服务器代码，负责接收客户端请求，处理数据块并返回反转结果。
test.txt: 客户端读取的输入文件。

运行环境
Python 3.11

客户端处理完成后，会在指定路径下生成反转后的文件 reversed_test.txt。

代码说明
TCPclient.py
TCPClient 类：
__init__(): 初始化客户端的各种属性。
get_user_input(): 获取用户输入的服务器信息和分块大小。
_validate_inputs(): 验证用户输入的参数是否合法。
read_input_file(): 读取指定文件的内容。
split_into_chunks(): 将文件内容分块。
connect_to_server(): 建立与服务器的 TCP 连接。
send_initialization_packet(): 发送初始化包并接收服务器同意包。
process_chunks(): 处理所有数据块，发送请求并接收反转结果。
_receive_packet(): 接收并解析数据包。
_receive_exact(): 接收精确长度的数据。
generate_output_file(): 生成反转后的文件。
close_connection(): 关闭 TCP 连接。
TCPserver.py
TCPServer 类：
__init__(): 初始化服务器的属性。
validate_port(): 验证端口号是否合法。
start_server(): 启动服务器并开始监听连接。
handle_connections(): 处理客户端连接的主循环。
_handle_client(): 处理单个客户端连接。
_receive_packet(): 精确接收指定大小的数据包。
shutdown(): 关闭服务器。

注意事项
请确保输入的 IP 地址、端口号、分块大小等参数在合法范围内。
输入文件 test.txt 必须存在于指定路径下。
服务器和客户端必须在同一网络中，或者服务器的 IP 地址和端口号可以被客户端访问。

贡献
如果你发现任何问题或有改进建议，请随时提交 issue 或 pull request。