import sqlite3
from random import shuffle, choice
from typing import Optional, List, Tuple

DATABASE_FILE = 'data/database.db'

def execute_query(query: str, params: Optional[tuple] = None, fetchall: bool = True) -> List[Tuple]:
    with sqlite3.connect(DATABASE_FILE) as con:
        cur = con.cursor() 
        try:
            if params is None: cur.execute(query)
            else: cur.execute(query, params)
            return cur.fetchall() if fetchall else []
        except sqlite3.Error as error:
            print(f"An error occurred: {error}")
            return []

def insert_player(player_id: int, username: str) -> None:
    query = 'INSERT INTO players (player_id, username, role, mafia_vote, citizen_vote, voted, dead, voted_for_finish_game) VALUES (?, ?, "Villager", 0, 0, 0, 0, 0)'
    execute_query(query, (player_id, username))

def return_players_amount() -> int:
    query = 'SELECT COUNT(*) FROM players'
    return execute_query(query, fetchall=True)[0][0]

def get_usernames(info: Optional[str] = None, alive: Optional[bool] = None) -> str:
    query = 'SELECT username FROM players'

    if info == 'mafia': query += ' WHERE LOWER(role)="mafia"'
    elif info == 'citizens': query += ' WHERE LOWER(role)="villager"'

    if alive:
        if 'WHERE' in query: query += ' AND dead=0'
        else: query += ' WHERE dead=0'

    data = execute_query(query, fetchall=True)
    return '\n'.join(row[0] for row in data)

def get_players_info() -> List[Tuple]:
    query = 'SELECT player_id, role, username FROM players'
    return execute_query(query, fetchall=True)

def get_all_alive() -> List[str]:
    query = 'SELECT username FROM players WHERE dead=0'
    data = execute_query(query, fetchall=True)
    return [row[0] for row in data]

def set_roles(players_amount: int) -> None:
    query_select = 'SELECT player_id FROM players'
    player_ids = execute_query(query_select, fetchall=True)

    game_roles = ['Villager'] * players_amount
    mafias_amount = int(players_amount * 0.3)
    for i in range(mafias_amount): game_roles[i] = 'Mafia'
    shuffle(game_roles)

    for role, row in zip(game_roles, player_ids):
        query_update = 'UPDATE players SET role=? WHERE player_id=?'
        execute_query(query_update, (role, row[0]))

def vote(type: str, username_to_kick: str, username_of_the_voter: str) -> bool:
    query_check_voter = 'SELECT username FROM players WHERE username=? AND voted=0 AND dead=0'
    voter_exists = execute_query(query_check_voter, (username_of_the_voter,)) # Проверка на право голоса
    
    if not voter_exists: return False

    query_check_target = 'SELECT username FROM players WHERE username=? AND dead=0'
    target_exists = execute_query(query_check_target, (username_to_kick,)) # Проверка на наличие в игре игрока, за которого собираются голосовать
    if target_exists:
        query_update_target: str = f'UPDATE players SET {type}={type}+1 WHERE username=?' # Добавление голоса игроку по типу голосования
        execute_query(query_update_target, (username_to_kick,))
        query_update_voter = 'UPDATE players SET voted=1 WHERE username=?' # Обновление параметров для запрета повторного голосования
        execute_query(query_update_voter, (username_of_the_voter,))
        return True
    return False

def vote_for_finish_game(username_of_the_voter: str) -> bool:
    query_check_voter = 'SELECT username FROM players WHERE username=? AND voted_for_finish_game=0' 
    if not execute_query(query_check_voter, (username_of_the_voter,)): return False # Проверка на право голоса
    query_update_voter = 'UPDATE players SET voted_for_finish_game=1 WHERE username=?' # Обновление параметров 
    execute_query(query_update_voter, (username_of_the_voter,))
    return True

def check_finish_vote() -> List[int]:
    number_of_players_to_complete = int(return_players_amount() * 0.7) 
    query_count_voted = 'SELECT COUNT(*) FROM players WHERE voted_for_finish_game=1' 
    voted_players = execute_query(query_count_voted, fetchall=True)[0][0] 
    return [voted_players, number_of_players_to_complete]

def presence_of_the_mafia_role(username: str) -> bool: 
    query_check_role = 'SELECT role FROM players WHERE username=? AND dead=0' 
    result = execute_query(query_check_role, (username,))
    return bool(result and result[0][0].lower() == 'mafia') 

def kill_players(vote_type: str) -> str:
    if vote_type == 'mafia': 
        vote_column = 'mafia_vote'
        role_condition = 'LOWER(role)="mafia"'
        vote_kill_coefficient = 0.5
    elif vote_type == 'citizen':
        vote_column = 'citizen_vote'
        role_condition = 'TRUE'
        vote_kill_coefficient = 0.15
    killed_player = 'Nobody'

    # Получение игроков, которые получили голос \ максимальное и минимальное количество голосов
    query_total_votes = f''' 
        SELECT
            COUNT(*) AS total_votes,
            MIN({vote_column}) AS min_vote,
            MAX({vote_column}) AS max_vote
        FROM players
        WHERE {vote_column} <> 0
    ''' 
    # Определение информации
    vote_info = execute_query(query_total_votes, fetchall=True)[0]
    total_votes = vote_info[0]
    min_vote_value = vote_info[1]
    max_vote_value = vote_info[2]

    number_of_players_to_kill = max(int(len(get_usernames(info=vote_type, alive=True)) * vote_kill_coefficient), total_votes) 

    # Получение информации о игроке и его количестве голосов в порядке убывания по имющимся голосам
    query_votes = f'''
        SELECT username, {vote_column}
        FROM players
        WHERE {vote_column} <> 0
        ORDER BY {vote_column} DESC
    '''
    players_and_their_received_votes = execute_query(query_votes, fetchall=True)
    
    killed_players = []
    if len(players_and_their_received_votes) == 1: # Если имеется только один игрок, за которого голосовали, то просто выполняется запрос  
        killed_player = players_and_their_received_votes[0][0]
        query_update_killed = 'UPDATE players SET dead=1 WHERE username=?'
        execute_query(query_update_killed, (killed_player,))
        killed_players.append(killed_player)
        
    if len(players_and_their_received_votes) > 1:
        remaining_players = []

        for player, votes in players_and_their_received_votes: # Выбор всех игроков, у которых больше минимального количества полученных голосов
            if number_of_players_to_kill == 0: break # Если лимит игроков на выбор был исчерпан то не за чем больше убивать
            if votes > min_vote_value:
                query_update_remaining = 'UPDATE players SET dead=1 WHERE username=?'
                execute_query(query_update_remaining, (player,))
                number_of_players_to_kill -= 1
                killed_players.append(player)
            else: remaining_players.append((player, votes)) # Если цикл дошел до игроков, которые имеют минимальное количество голосов, то они добавляются в новый список для рандомной выборки и выбора

        while number_of_players_to_kill > 0 and remaining_players: # Пока не исчерпан лимит на убийство и в списке есть кого выбирать
            random_player_data = choice(remaining_players) 
            query_update_random = 'UPDATE players SET dead=1 WHERE username=?'
            execute_query(query_update_random, (random_player_data[0],))
            number_of_players_to_kill -= 1
            killed_players.append(random_player_data[0])
            remaining_players.remove(random_player_data)

    return killed_players

def clear(dead: Optional[bool] = False) -> None: 
    query_clear = 'UPDATE players SET citizen_vote=0, mafia_vote=0, voted=0, voted_for_finish_game=0'
    if dead: query_clear += ', dead=0'
    execute_query(query_clear)

def check_winner() -> Optional[str]:
    query_mafia_count = 'SELECT COUNT(*) FROM players WHERE LOWER(role)="mafia" AND dead=0'
    mafias_amount = execute_query(query_mafia_count, fetchall=True)[0][0]
    query_citizen_count = 'SELECT COUNT(*) FROM players WHERE LOWER(role)<>"mafia" AND dead=0'
    citizens_amount = execute_query(query_citizen_count, fetchall=True)[0][0]

    if mafias_amount > citizens_amount / 2: return 'mafia'
    elif mafias_amount == 0: return 'citizens'
    else: return None

def player_in_lobby_availability_check(player_id: int, username: str) -> bool:
    query_check_availability = 'SELECT * FROM players WHERE player_id=? AND username=?'
    availability = execute_query(query_check_availability, (player_id, username), fetchall=True)
    return bool(availability)

def kick_player_from_lobby(player_id: int, username: str) -> None:
    query_kick_player = 'DELETE FROM players WHERE player_id=? AND username=?'
    execute_query(query_kick_player, (player_id, username))

