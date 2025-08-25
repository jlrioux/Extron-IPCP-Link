


from extronlib.engine import IpcpLink
link = IpcpLink('172.16.1.10','AVLAN')

from extronlib import event
from extronlib.device import UIDevice
from extronlib.ui import Slider,Button,Label

ui = UIDevice('ConnectFourPanel')
ui.ShowPage('Main')

red_slider_ids = list(range(1,8))
yellow_slider_ids = list(range(11,18))
col_button_ids = list(range(21,28))
position_button_ids = list(range(101,143))


red_sliders = [] #type:list[Slider]
yellow_sliders = [] #type:list[Slider]
slider_values = [] #type:list[int]
btn_drops = [] #type:list[Button]
position_buttons = [] #type:list[list[Button]]

row_positions = [95,79,67,55,43,31,20,0]
row_positions.reverse()


def create_drop_button_event(id):
    def e(button,state):
        global slider_values
        drop_piece(id)
    return e
for id in range(7):
    slider_values.append(0)
    red_sliders.append(Slider(ui,id+1))
    yellow_sliders.append(Slider(ui,id+11))
    btn_drops.append(Button(ui,id+21))
    btn_drops[id].Pressed = create_drop_button_event(id)
btn_reset = Button(ui,41)
@event(btn_reset,'Pressed')
def e(button,state):
    reset_board()


cur = 0
num_rows = 6
num_cols = 7
board = [] #type:list[list[bool]]
position_buttons = [] #type:list[list[Button]]
for row in range(num_rows):
    board.append([])
    position_buttons.append([])
    for col in range(num_cols):
        board[row].append(None)
        position_buttons[row].append(Button(ui,position_button_ids[cur]))
        cur += 1
player1turn = True
def set_drop_buttons():
    for col in range(num_cols):
        red_sliders[col].SetFill(0)
        yellow_sliders[col].SetFill(0)
        btn_drops[col].SetState({True:1,False:2}[player1turn])

def reset_board():
    global board
    global player1turn
    for row in range(num_rows):
        for col in range(num_cols):
            board[row][col] = None
            position_buttons[row][col].SetState(0)
    for col in range(num_cols):
        red_sliders[col].SetFill(0)
        yellow_sliders[col].SetFill(0)
        btn_drops[col].SetState(0)
    player1turn = True
    set_drop_buttons()


def drop_piece(col_to_drop):
    global board
    global player1turn
    import time
    start = 95
    stop_position = determine_bottom_row(col_to_drop)
    if stop_position < 0:return
    for col in range(num_cols):
        btn_drops[col].SetState(0)
    if player1turn:sliders = red_sliders
    else:sliders = yellow_sliders
    stop = row_positions[stop_position]
    cur = start
    for step in range(stop,start+1):
        cur = cur-1
        sliders[col_to_drop].SetFill(cur)
        time.sleep(0.01)
    position_buttons[num_rows-stop_position][col_to_drop].SetState({True:1,False:2}[player1turn])
    sliders[col_to_drop].SetFill(0)
    if check_for_winner() is None:
        player1turn = not player1turn
        set_drop_buttons()

def determine_bottom_row(col):
    for row in range(num_rows):
        if board[row][col] is None:
            board[row][col] = player1turn
            return row+1
    return -1

def check_for_winner():
    #print the board
    count = num_rows-1
    for row in board:
        #print(board[count])
        count -= 1
    for row in range(num_rows):
        for col in range(num_cols):
            if board[row][col] is None:continue
            result = check_node_up(row,col,1)
            if result is None:
                result = check_node_right(row,col,1)
            if result is None:
                result = check_node_up_right(row,col,1)
            if result is None:
                result = check_node_up_left(row,col,1)
            if result is not None:break
        if result is not None:break

    if result is not None:
        states = {True:1,False:2}
        for row in range(num_rows):
            for col in range(num_cols):
                position_buttons[row][col].SetState(states[result])
    return result
def check_node_up(row,col,depth):
    if board[row][col] is None:return None
    result = None
    if row < num_rows-1:
        if board[row+1][col] == board[row][col]:
            if depth < 3:
                result = check_node_up(row+1,col,depth+1)
                if result is not None:return result
            else:return board[row][col]
    return result
def check_node_right(row,col,depth):
    if board[row][col] is None:return None
    result = None
    if col < num_cols-1:
        if board[row][col+1] == board[row][col]:
            if depth < 3:
                result = check_node_right(row,col+1,depth+1)
                if result is not None:return result
            else:return board[row][col]
    return result
def check_node_up_right(row,col,depth):
    if board[row][col] is None:return None
    result = None
    if row < num_rows-1 and col < num_cols-1:
        if board[row+1][col+1] == board[row][col]:
            if depth < 3:
                result = check_node_up_right(row+1,col+1,depth+1)
                if result is not None:return result
            else:return board[row][col]
    return result
def check_node_up_left(row,col,depth):
    if board[row][col] is None:return None
    result = None
    if row < num_rows-1 and col > 0:
        if board[row+1][col-1] == board[row][col]:
            if depth < 3:
                result = check_node_up_left(row+1,col-1,depth+1)
                if result is not None:return result
            else:return board[row][col]
    return result


reset_board()

print('ready')

