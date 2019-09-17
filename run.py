import sys
import time
import numpy as np
from game import Connect6, Connect6WJS
from player import RandomBot, Player, MyPolicy

def run():
    # 设置棋盘维度
    BOARD_DIMENSION = 21
    print('Welcome to Keavnn\'s Connect6.')
    print('Choose now_player slot. (1=Player 2=AI)')
    
    player1_choice, player2_choice = '2', '2'
    player1_name, player2_name = 'Keavnn', 'BlueFisher'
    # player1_choice, player1_name = input(' Player1 (1 or 2) : '), input(' Player1 name: ')
    # player2_choice, player2_name = input(' Player2 (1 or 2) : '), input(' Player2 name: ')
    player1_param = {'dim': BOARD_DIMENSION, 'name': player1_name}
    player2_param = {'dim': BOARD_DIMENSION, 'name': player2_name}

    model1 = Player(**player1_param) if player1_choice == '1' else MyPolicy(**player1_param)
    time.sleep(1)   # 避免log写在同一个文件
    model2 = Player(**player2_param) if player2_choice == '1' else RandomBot(**player2_param)
    
    players = [model1, model2]
    env = Connect6WJS(BOARD_DIMENSION)
    loop(env, players)
    

def loop(env, players):
    info = ['黑子', '白子']
    offset = [2, 1] # 在将可选动作转为one_hot时，需要把棋盘无子位置转换成己方一子，offset用于将无子转为自己的子，如黑子，2-offset[0]=0，即为黑子
    wins = [0, 0]   # 用于统计每位玩家获胜的次数

    for episode in range(10000):
        if np.random.rand() > 0.5:
            players.reverse()
            wins.reverse()
        for i in range(2):
            if isinstance(players[i], MyPolicy):
                players[i].update_offset(offset[i])

        env.register(players[0].name, players[-1].name)

        state = env.reset()
        now_player = 0  # 用于记录当前执子的选手
        move_step = 1   # 用于记录该玩家走了几步，2步需换对方执子
        total_step = 0  # 用于记录总的步数
        states = [
            [state, state],  # 黑棋状态
            [state, state],  # 白棋状态
        ]

        while True:
            total_step += 1
            # env.render()
            while True:  # 如果选择的动作不合法，就重新选择。这个一般只对随机智能体或者手动输入时使用，实现自己的智能体时可以根据需求计算出每一步的可行动空间，避免重新选择动作
                try:
                    x, y = players[now_player].choose_action(state)
                    # print(f'{players[now_player].name}选择, x: {x+1}, y: {y+1}')
                    is_ok, msg = env.can_place(x, y)
                    if not is_ok:
                        # print(f'{msg}, 请换个位置')
                        continue
                    break
                except KeyboardInterrupt:
                    print('游戏中断')
                    sys.exit()

            state = env.step(x, y)
            env.sendBoardtoUnity()
            #time.sleep(1)
            #print(env.)
            states[now_player][-1] = state
            move_step += 1
            if wins[now_player] - wins[(now_player + 1)%2] < 6:
                players[now_player].learn()    # 如果想让AI每两步学习一次，可以将其放置在下方判断中

            result = env.is_over()
            if result is not None:
                if result == -1:
                    r0, r1= 0.1, 0.1
                    print(f'episode: {episode}, step: {total_step:>3d}, 平局')
                else:
                    r0, r1 = 1, -move_step
                    print(f'episode: {episode:>4d}, step: {total_step:>3d}, {info[now_player]}{players[now_player].name}获胜')
                    wins[now_player] += 1

                players[now_player].store(s=states[now_player][0], r=r0, s_=states[now_player][1], done=True)
                players[now_player].writer_loop_summary(episode, reward=r0, step=total_step)
                next_player = (now_player + 1) % 2
                players[next_player].store(s=states[next_player][0], r=r1, s_=states[next_player][1], done=True)
                players[next_player].writer_loop_summary(episode, reward=r1, step=total_step)
                # env.render()
                # print(env.last_move + 1)
                # print(f'游戏结束，{players[now_player].name}获胜')
                break

            if move_step == 2:
                move_step = 0
                now_player = (now_player + 1) % 2
                players[now_player].store(s=states[now_player][0], r=0, s_=states[now_player][1], done=False)
                states[now_player][0] = states[(now_player + 1) % 2][1]

if __name__ == '__main__':
    run()
