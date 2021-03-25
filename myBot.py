#!/usr/bin/env python3

import requests
import json
import random
import sys

# Must install python-chess for the following
import chess
import chess.engine


# Global variables

TOKEN = 'KAYCsLsYPDllbW53'
NAME  = 'demegara'
API   = 'https://lichess.org/api/'
AUTH  = { 'Authorization': 'Bearer ' + TOKEN }


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

            # If the challenge has not been accepted after 3 cycles, cancel it
            counter += 1
            if counter >= 3:
                cancel_challenge(gameID)
                s.close()
                return False

            if line:
                info = json.loads(line)

                if info.get('type') == 'gameStart' and info.get('game').get('id') == gameID:
                    s.close()
                    return True

                elif info.get('type') == 'challengeDeclined' and info.get('challenge').get('id') == gameID:
                    s.close()
                    return False

    s.close()
    return False


def play_game(gameID, moveSelector):
    '''
      Play a game which has started.
        Input:
             gameID (game identifier)

        No output
    '''

    s = requests.Session()

    with s.get(API + 'bot/game/stream/' + gameID, headers = AUTH, stream = True) as answer:

        for line in answer.iter_lines():
            if line:
                print(line, flush = True)
                info = json.loads(line)
                state = info.get('state')

                # Get the color our BOT is playing with
                if state:
                    color = info.get('white').get('id') == NAME

                else:
                    state = info

                # If the game is finished, terminate
                if state.get('status') != 'started':
                    s.close()
                    return

                moves = state.get('moves', '')

                # FIXME: It would be good not to go through all moves each time
                b = chess.Board()
                if len(moves) > 0:
                    for move in moves.split(' '):
                        b.push_uci(move)

                # Continue the loop if it is not the BOT's turn
                if b.turn != color:
                    continue

                # Pick a move using the moveSelector
                m = moveSelector(b)

                requests.post(API + 'bot/game/' + gameID + '/move/' + str(m), headers = AUTH)

    s.close()


def randomMove(board):
    '''
      Pick a random move from the given board
        Input:
             board (chess.Board type, from python-chess)

        Output:
             move (chess.Move.from_uci type, from python-chess)
    '''
    return random.choice([m for m in board.legal_moves])


if __name__ == '__main__':

    user = sys.argv[1]
    gameID = challenge_user(user, increment = 3, rated = False)

    if wait_for_starting_game(gameID):
        play_game(gameID, randomMove)
