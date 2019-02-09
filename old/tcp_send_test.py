import socket
import sys
import threading
import time

def listen(sock):
    while True:
        # 서버로부터 수신
        # time.sleep(0.1)
        print("수신대기")
        rbuff = sock.recv(1024)  # 메시지 수신
        received = str(rbuff, encoding='utf-8')
        print('수신 : {0}'.format(received))
 


if __name__ == '__main__':
    # if len(sys.argv) < 4:
    #     print('{0} <Bind IP> <Server IP> <Message>'.format(sys.argv[0]))
    #     sys.exit()

    bindIP = '0.0.0.0'
    serverIP = '192.168.0.53'
    message = '11'

    direction = sys.argv[1]
    if direction == '0':
        _d = '01'
    else:
        _d = '10'

    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_STREAM)  # SOCK_STREAM은 TCP socket을 뜻함
    sock.bind((bindIP, 0))
    try:
        sock.connect((serverIP, 8250))  # 서버에 연결 요청
    finally:
        t = threading.Thread(target=listen, args=(sock,))
        t.start()
        while True:
            try:
                # _m = input("Msg:")
                _m = "STX"+_d+"100111001110004ETX"

                # 서버로 송신
                sbuff = bytes(_m, encoding='utf-8')
                sock.send(sbuff)  # 메시지 송신
                print('송신 {0}'.format(_m))

                time.sleep(0.1)
                
            except Exception as ex:
                print("Error",ex)
                break
            # finally:
            #     socket.close()