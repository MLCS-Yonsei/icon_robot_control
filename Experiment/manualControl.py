import curses, time, socket


# --------------------------------------
def input_char(message):
    try:
        win = curses.initscr()
        win.addstr(0, 0, message)
        while True:
            ch = win.getch()
            if ch in range(32, 127): break
            time.sleep(0.05)
    except:
        raise
    finally:
        curses.endwin()
    return chr(ch)


# --------------------------------------

robot_ip = "192.168.0.53"
print("Connecting to robot", robot_ip)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.bind(("0.0.0.0", 0))
client_socket.connect((robot_ip, 8250))
print("Connected to the robot.")

hor_direction = '11'
robot_speed = '050'
hor_speed = '020'
ver_direction = '11'
ver_speed = '030'
robot_face = '01'
hor_head_direction = '11'

while True:
    c = input_char('Press s or n to continue:')
    if c.upper() == 'C':
        hor_direction = '10'
        hor_head_direction = '01'
    elif c.upper() == 'Z':
        hor_direction = '01'
        hor_head_direction = '10'
    elif c.upper() == 'X':
        hor_direction = '11'
        hor_head_direction = hor_direction
    elif c.upper() == 'A':
        hor_direction = '11'
        hor_speed = '035'
        hor_head_direction = '10'
    elif c.upper() == 'D':
        hor_direction = '11'
        hor_speed = '035'
        hor_head_direction = '01'
    elif c.upper() == 'S':
        hor_direction = '11'
        hor_speed = '020'
        hor_head_direction = hor_direction
    elif c.upper() == 'E':
        hor_direction = '11'
        hor_head_direction = '11'
        ver_direction = '10'
    elif c.upper() == 'Q':
        hor_direction = '11'
        hor_head_direction = '11'
        ver_direction = '01'
    elif c.upper() == 'W':
        hor_direction = '11'
        hor_head_direction = hor_direction
        ver_direction = hor_direction
    elif c.upper() == '1':
        robot_face = '01'
    elif c.upper() == '2':
        robot_face = '02'
    elif c.upper() == '3':
        robot_face = '03'
    elif c.upper() == '4':
        robot_face = '04'
    elif c.upper() == '5':
        robot_face = '05'
    elif c.upper() == '6':
        robot_face = '06'
    elif c.upper() == '7':
        robot_face = '07'
    elif c.upper() == '8':
        robot_face = '08'
    elif c.upper() == '9':
        robot_face = '09'
    elif c.upper() == 'B':
        robot_speed = '050'
    elif c.upper() == 'N':
        robot_speed = '070'
    elif c.upper() == 'M':
        robot_speed = '100'
    else:
        pass

    msg = "".join(
        ['STX', hor_direction, robot_speed, hor_head_direction, hor_speed, ver_direction, ver_speed, robot_face, 'ETX'])
    client_socket.send(msg.encode())