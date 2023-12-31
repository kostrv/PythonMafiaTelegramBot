from db import return_players_amount, get_usernames

main_info_message = '''
Игра "Мафия"

Цель игры:
Для мирных: выявить и уничтожить всех представителей мафии.
Для мафии: остаться незамеченной и убить мирных, чтобы уравновесить силы.

Роли:
Мафия: Цель - убивать мирных. Знают друг друга.
Мирные: Цель - выявить мафию и убрать её. Знают только свою роль.

Игровой процесс:
Раздача ролей:
Каждый игрок получает личное сообщение с указанием его роли (мафия, мирный).

1. Ночь:
Мафия выбирает одного игрока для убийства. На это дается 60 секунд. 
Если будут игроки с разным количеством голосом от мафии, будет выбрано нужное количество для выбывания.

2. Утро:
Объявляются результаты ночных действий: убитые игроки, успешно леченные, результаты проверки комиссара.
Голосование:
Голосование проводится только через личный чат с ботом.
Игроки голосуют за подозреваемого в мафии.
Игрок с наибольшим числом голосов выбывает.

3. День:
Обсуждение результатов голосования и стратегии.
Игроки могут высказывать подозрения и аргументировать свои действия.
Проверка на завершение игры:

Игра продолжается до тех пор, пока не выполнено условие победы для мирных или мафии.

Завершение игры:
Объявляется победитель (мирные или мафия).
Возможность начать новую игру.

Как играть.
- Чтобы начать полноценное использование бота, необходимо добавить его в групповой чат.\n
- Чтобы зайти в лобби для игры, напишите команду /ready в личные сообщения боту.\n
- Для игры необходимо минимум 6 человек.\n
- Обязательное условие: для игры необходимо иметь с открытый чат с ботом в личных сообщениях, иначе вы будете кикнуты из лобби при начале игры.\n
- Для просмотра основных команд пропишите /commands.\n
- Игру можно прервать, если за это проголосуют большинство игроков.\n
'''

commands_info = '''
Команды:
/info - об игре\n
/ready - вход в игру (Доступно только в лс бота)\n
/leave - покинуть лобби\n
/lobby - просмотр участников\n
/game - Начать игру\n
/kick - проголосовать за кик игрока\n
/kill - проголосовать за убийство игрока (доступно только за мафию)\n
/finish - проголосовать за досрочное окончание игры\n
'''

start_message = '''
Этот бот предназначен для игры в мафию.
'''

lobby_info_message = f'''
Количество игроков: {return_players_amount()}
Все игроки:
{get_usernames()}
    '''

go_to_lobby_message = '''
Для того, чтобы войти в лобби, пропишите /ready.
Важно: если вы каким либо образом ограничите возможность бота отправлять вам сообщения, 
то будете автоматически удалены из лобби при начале игры. 
/info - помощь.
'''

create_game_message = '''
Для создания игры необходимо добавить бота в групповой чат.
Далее, после присоединения игроков к лобби, вы можете начать игру, используя команду /game.
/info - помощь.
'''
