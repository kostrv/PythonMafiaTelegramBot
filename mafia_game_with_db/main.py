from db import insert_player, return_players_amount, set_roles, get_players_info, get_usernames, get_all_alive, vote, vote_for_finish_game, check_finish_vote, presence_of_the_mafia_role, kill_players, check_winner, clear, kick_player_from_lobby, player_in_lobby_availability_check
from telebot import TeleBot, types
from time import sleep
from info_messages import *

TOKEN = ''
bot = TeleBot(TOKEN)
game: bool = False
night: bool  = True

def check_chat_type(message, chat_types: list) -> bool: 
    if message.chat.type in chat_types: return True
    else: 
        bot.send_message(message.chat.id, text=f'Данная функция недоступна в чате, который не является {chat_types[0]}')
        return False

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == 'go_to_lobby': bot.send_message(call.message.chat.id, text=go_to_lobby_message)
    elif call.data == 'create_game': bot.send_message(call.message.chat.id, text=create_game_message)

'================================================================================INFO STUFF================================================================================'
@bot.message_handler(commands=['start'])
def show_start_info(message) -> None:
    if not check_chat_type(message=message, chat_types=['private']): return
    keyboard = types.InlineKeyboardMarkup()
    messages = ['Войти в лобби.', 'Создать свою игру.']
    callback_result = ['go_to_lobby', 'create_game']

    for btn_id, btn_text in enumerate(messages): keyboard.add(types.InlineKeyboardButton(text=btn_text, callback_data=callback_result[btn_id]))

    bot.send_message(message.chat.id, text=start_message, reply_markup=keyboard)

@bot.message_handler(commands=['info'])
def show_info(message) -> None: bot.send_message(message.chat.id, text=main_info_message)

@bot.message_handler(commands=['commands'])
def show_commands(message) -> None: bot.send_message(message.chat.id, text=commands_info)

@bot.message_handler(commands=['lobby'])
def show_lobby_info(message) -> None: bot.send_message(message.chat.id,text=lobby_info_message)


'================================================================================MAIN GAME STUFF================================================================================'
def action_timer(chat_id, duration: int, interval: int) -> None:
    remaining_time = duration
    while remaining_time > 0:
        if remaining_time % interval == 0: bot.send_message(chat_id, f'Осталось {remaining_time} секунд.')
        sleep(1)
        remaining_time -= 1

def game_loop(message) -> None:
    global night, game
    bot.send_message(message.chat.id, text='Добро пожаловать в игру. Матч начнется через 30 секунд. /info - Все об игре.')
    action_timer(chat_id=message.chat.id, duration=60, interval=20)
    bot.send_message(message.chat.id, text='Матч начинается!')
    game = True
    
    while game:     
        if night:
            bot.send_message(message.chat.id, 'Наступила ночь.\n\nИгроки мафии могут начать голосование.')  
            action_timer(chat_id=message.chat.id, duration=60, interval=20)
            bot.send_message(message.chat.id, 'Время ночи закончилось.')
        else:
            bot.send_message(message.chat.id, 'Город просыпается, наступил день. \n\nИгроки могут начать обсуждение и голосование.')
            action_timer(chat_id=message.chat.id, duration=60, interval=20)
            bot.send_message(message.chat.id, 'Голосование окончено.')

        bot.send_message(message.chat.id, text=get_killed(night=night))

        winner: str | None = check_winner()
        if winner != None:
            if winner == 'citizens':
                bot.send_message(message.chat.id, 'Победили мирные жители.')
            elif winner == 'mafia': 
                bot.send_message(message.chat.id, 'Победила мафия.')
            clear(dead=True)  
            game = False
            night = True
            break
        
        # Сброс
        clear(dead=False)   
        night = not night
        alive = get_all_alive()
        alive = '\n'.join(alive)
        bot.send_message(message.chat.id, f'В игре:\n{alive}')

'================================================================================GAME START================================================================================'
@bot.message_handler(func=lambda m: m.chat.type == 'private', commands=['ready'])
def login_into_game(message) -> None:
    if player_in_lobby_availability_check(player_id=message.from_user.id, username=message.from_user.first_name): 
        bot.send_message(message.chat.id, text=f'Вы уже являетесь участником лобби. \n/leave - выход.')
        return
    if game: 
        bot.send_message(message.chat.id, text=f'Невозможно войти в игру, когда матч уже начался. \nПовторите попытку позже.')
        return
    bot.send_message(message.chat.id, text=f'Пользователь {message.from_user.first_name} добавлен в игру. \n/leave - выход.')
    bot.send_message(message.chat.id, text=f'Количество игроков: {return_players_amount()+1} \n(Минимум 6).')
    insert_player(player_id=message.from_user.id, username=message.from_user.first_name)

@bot.message_handler(commands=['leave'])
def leave_from_lobby(message) -> None: 
    if player_in_lobby_availability_check(player_id=message.from_user.id, username=message.from_user.first_name): 
        kick_player_from_lobby(player_id=message.from_user.id, username=message.from_user.first_name)
        bot.send_message(message.chat.id, text=f'Игрок {message.from_user.first_name} покинул лобби.')
    else: bot.send_message(message.chat.id, text=f'Игрок {message.from_user.first_name} не является участником лобби.')

@bot.message_handler(commands=['game'])
def start_game(message) -> None:
    global game
    kicked_players: list = []
    if not check_chat_type(message=message, chat_types=['group', 'supergroup']): return

    if game:
        bot.send_message(message.chat.id, text='Игра уже началась!')
        return
    players: int = return_players_amount()
    if players >= 6 and not game:
        set_roles(players)
        players_game_data = get_players_info()
        mafia_usernames = get_usernames(info='mafia')
        for player_data in players_game_data:
            # player_data - (id,role,username)
            if player_data[1] == 'Mafia': role_message = f'Ваша роль - Мафия. Все игроки мафии: \n{mafia_usernames}'
            else: role_message = 'Ваша роль - Горожанин.'
            try: bot.send_message(int(player_data[0]), role_message)
            except:
                kick_player_from_lobby(player_id=player_data[0], username=player_data[2])
                kicked_players.append(player_data[2])
        
        if kicked_players: bot.send_message(message.chat.id, text=f'Возникла проблема с добавлением в игру: \n{", ".join(kicked_players)}')
        game_loop(message=message)

    else: bot.send_message(message.chat.id, text='Недостаточно людей для игры!')

'================================================================================GAME COMMANDS================================================================================'
@bot.message_handler(commands=['finish'])
def finish_game(message) -> None:
    global game
    result_of_vote = vote_for_finish_game(username_of_the_voter=message.from_user.username)
    if not result_of_vote: bot.send_message(message.chat.id, text='У вас больше нет права голосовать.')
    else: bot.send_message(message.chat.id, text='Ваш голос учитан.')
    finish_vote_data = check_finish_vote()
    if finish_vote_data[0] >= finish_vote_data[1]: 
        bot.send_message(message.chat.id, text='Игра завершена досрочно результатом голосования. \n/game - начать новую игру')
        clear(dead=True) 
        game = False
    else: bot.send_message(message.chat.id, text=f'Для прерывания игры необходимо еще {finish_vote_data[1]-finish_vote_data[0]} голосов.')

def common_vote_logic(message, vote_type: str, chat_types: list) -> None:
    global game, night
    if not check_chat_type(message=message, chat_types=chat_types): return
    
    username_for_action = ' '.join(message.text.split(' ')[1:])
    usernames = [username.lower() for username in get_all_alive()]
    mafia_usernames = [username.lower() for username in get_usernames(info='mafia', alive=True)]

    if game:
        if not username_for_action.lower() in usernames: 
            bot.send_message(message.chat.id, f'Такого имени как {username_for_action} нет либо игрок уже выбыл из игры.')
            return
        if vote_type == 'citizen_vote':
            if night: 
                bot.send_message(message.chat.id, 'Во время ночи нельзя голосовать.') 
                return
        elif vote_type == 'mafia_vote':
            if not presence_of_the_mafia_role(message.from_user.username):
                bot.send_message(message.chat.id, 'Вы не являетесь мафией или вы выбыли из игры.')
                return  
            if not night:
                bot.send_message(message.chat.id, 'Во время дня нельзя голосовать за жертву.') 
                return
            if username_for_action.lower() in  mafia_usernames:
                bot.send_message(message.chat.id, f'Вы не можете голосовать за убийство игрока {username_for_action}, поскольку он также является мафией.')
                return
            
        voting = vote(type=vote_type, username_to_kick=username_for_action, username_of_the_voter=message.from_user.username)
        if voting: bot.send_message(message.chat.id, 'Ваш голос учитан.')
        else: bot.send_message(message.chat.id, 'У вас больше нет права голосовать.')
        
    else: bot.send_message(message.chat.id, 'Игра еще не началась.')

@bot.message_handler(commands=['kick'])
def kick(message) -> None: common_vote_logic(message, vote_type='citizen_vote', chat_types=['private'])

@bot.message_handler(commands=['kill'])
def kill(message) -> None: common_vote_logic(message, vote_type='mafia_vote', chat_types=['private'])
    
def get_killed(night: bool) -> str:
    if not night: 
        killed_players = kill_players(vote_type="citizen")
        if not killed_players: return 'Сегодня никого не выгнали'
        killed_players_str = '\n'.join(killed_players)
        return f'Жители выгнали: \n{killed_players_str}'
    
    killed_players = kill_players(vote_type="mafia")
    if not killed_players: return 'За эту ночь никого не убили'
    
    killed_players_str = '\n'.join(killed_players)
    return f'Мафия убила: \n{killed_players_str}'

if __name__ == '__main__':
    bot.polling(none_stop=True) 

