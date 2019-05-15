from socket import *

serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.bind(('', 8250))

while True:
    print("listening...")
    serverSock.listen(1)
    clientSock, addr = serverSock.accept()

    while True:
        try:
            print("communicating..")
            clientSock.recv(100)
            clientSock.send("STX0,0,0,0,0ETX".encode())
        except:
            break