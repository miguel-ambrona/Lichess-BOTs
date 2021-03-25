#!/usr/bin/env python3
# juanro04@ucm.es

import requests
import json
import random
import time
import sys

import chess # python-chess
import chess.engine

#TOKEN = 'CC06q69Dzr1YZJ1i'
#NAME  = 'henr-chinaski'
TOKEN = 'KAYCsLsYPDllbW53'
NAME  = 'demegara'
API   = 'https://lichess.org/api/'
AUTH  = { 'Authorization': 'Bearer ' + TOKEN }

#stockfish = chess.engine.SimpleEngine.popen_uci('../opening-trainer/Stockfish/src/stockfish')
#stockfish.configure({"Threads": 4})

# def analyze(board, ms):

#     global stockfish
#     limit = chess.engine.Limit(time = ms / 1000)
#     #limit = chess.engine.Limit(depth = 2)
#     info = stockfish.analyse(board, limit)

#     try:
#         best = info['pv'][0]
#     except:
#         best = None

#     return best

def challenge_user(username, rated = False, seconds = 300, increment = 0):
    '''
      Challenge a user to a game.
        Input:
             username (name of the user to be challenged)
                rated (optional, Boolean indicating whether the game is rated)
              seconds (optional, clock initial time in seconds)
            increment (optional, clock increment in seconds)

        Output:
               gameID (challenge identifier, which will be the game identifier if accepted)

    '''

    parameters = { 'rated' : 'true' if rated else 'false', 'clock.limit' : seconds, 'clock.increment' : increment }
    answer = requests.post(API + 'challenge/' + username, headers = AUTH, data = parameters)
    info = json.loads(answer.text)
    return info['challenge']['id']


def cancel_challenge(gameID):
    '''
      Cancel a challenge.
        Input:
             gameID (challenge identifier)

        No output
    '''

    answer = requests.post(API + 'challenge/' + gameID + '/cancel', headers = AUTH)
    info = json.loads(answer.text)


def wait_for_starting_game(gameID):
    '''
      Execute this function after having sent a challenge has been created with 'challenge_user'.
        Input:
             gameID (resulting from the challenge_user call).

        Output:
            Boolean (true) if the challenge was accepted, (false) if it was aborted
    '''

    s = requests.Session()
    with s.get(API + 'stream/event', headers = AUTH, stream = True) as answer:

        counter = 0
        for line in answer.iter_lines():

            # If the challenge has not been accepted after 5 cycles, cancel it
            counter += 1
            if counter > 5:
                cancel_challenge(gameID)
                s.close()
                return False

            # Continue if there is no new events
            if len(line) == 0:
                continue

            info = json.loads(line)

            if info.get('type') == 'gameStart' and info.get('game').get('id') == gameID:
                s.close()
                return True

            elif info.get('type') == 'challengeDeclined' and info.get('challenge').get('id') == gameID:
                s.close()
                return False

    s.close()
    return False

def play_game(gameID):

    s = requests.Session()
    with s.get(API + 'bot/game/stream/' + gameID, headers = AUTH, stream = True) as answer:

        for line in answer.iter_lines():
            if line:
                info = json.loads(line)

                print(info, flush=True)

                if info.get('error'):
#                    continue
                    time.sleep(5)
                    play_game(gameID)
                    return

                state = info.get('state')

                if state:
                    color = info.get('white').get('id') == NAME
                    print('COLOR', color)

                else:
                    state = info

                if state.get('status') != 'started':
                    return

                moves = state.get('moves', '')

                b = chess.Board()

                if len(moves) > 0:
                    for move in moves.split(' '):
                        b.push_uci(move)

                if b.turn != color:
                    continue

                m = random.choice([m for m in b.legal_moves])
                #m = analyze(b, 1000)

                requests.post(API + 'bot/game/' + gameID + '/move/' + str(m), headers = AUTH)

                print(b, flush=True)

    s.close()


if __name__ == '__main__':

    try:
        user = sys.argv[1]
    except:
        user = 'ambrona'

    gameID = challenge_user(user)

    a = wait_for_starting_game(gameID)
    print("HOLA", a, flush = True)
    if a:
        play_game(gameID)

    print("HERE")
