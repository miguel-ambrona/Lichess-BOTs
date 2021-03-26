#!/usr/bin/env python3

import requests
import json
import random
import sys

# Must install python-chess for the following
import chess
import chess.engine


# Global variables

#TOKEN = 'KAYCsLsYPDllbW53'
#NAME  = 'demegara'
TOKEN = 'oaUsKX1NPwk1PyBg'
NAME  = 'clubajedrezchamberi'
API   = 'https://lichess.org/api/'
AUTH  = { 'Authorization': 'Bearer ' + TOKEN }

STOCKFISH = chess.engine.SimpleEngine.popen_uci('./Stockfish/src/stockfish')


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


def accept_challenge(gameID):
    '''
      Accept a challenge.
        Input:
             gameID (challenge identifier)

        No output
    '''

    answer = requests.post(API + 'challenge/' + gameID + '/accept', headers = AUTH)
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


def play_game(gameID, moveSelector, chatMessenger):
    '''
      Play a game which has started.
        Input:
                gameID (game identifier)
         moveoSelector (function that takes a chess.Board and outputs a chess.Board.Move.from_uci)
         chatMessenger (function that takes a chess.Board and outputs a string or None)

        No output
    '''

    s = requests.Session()

    with s.get(API + 'bot/game/stream/' + gameID, headers = AUTH, stream = True) as answer:

        for line in answer.iter_lines():
            if line:
                print(line, flush = True)
                info = json.loads(line)
                state = info.get('state')

                # Check if we got a message from the chat and continue in that case
                if info.get('type') == 'chatLine':
                    continue

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

                # Possibly write in the chat
                msg = chatMessenger(b)
                if msg:
                    parameters = { 'room' : 'player', 'text' : msg }
                    requests.post(API + 'bot/game/' + gameID + '/chat', headers = AUTH, data = parameters)

                # Continue the loop if it is not the BOT's turn
                if b.turn != color:
                    continue

                # Pick a move using the moveSelector
                m = moveSelector(b)

                requests.post(API + 'bot/game/' + gameID + '/move/' + str(m), headers = AUTH)

    s.close()


def random_move(board):
    '''
      Pick a random move from the given board
        Input:
             board (chess.Board type, from python-chess)

        Output:
             move (chess.Move.from_uci type, from python-chess)
    '''
    return random.choice([m for m in board.legal_moves])


def analyze(board, searchDepth = 10, outputInfo = False, multiPV = 1):
    '''
      Pick a move using Stockfish at a low depth
        Input:
             board (chess.Board type, from python-chess)

        Output:
             move (chess.Move.from_uci type, from python-chess)
    '''

    global STOCKFISH
    limit = chess.engine.Limit(depth = searchDepth)

    info = STOCKFISH.analyse(board, limit, multipv = multiPV)
    output = []

    for info_move in info:

        try:
            best = info_move['pv'][0]
        except:
            best = None

        score = info_move['score'].relative.score(mate_score = 10**6)

        if outputInfo:
            output.append({ 'move' : best, 'score' : score })

        else:
            output.append(best)

    if multiPV > 1:
        return output
    else:
        return output[0]


def weak_engine(board):
    '''
      Weak engine that picks a move
        Input:
             board (chess.Board type, from python-chess)

        Output:
             move (chess.Move.from_uci type, from python-chess)
    '''

    # If there is only a good move, play it

    moves = analyze(board, searchDepth = 10, outputInfo = True, multiPV = 9)
    refScore = moves[0]['score']

    N = 0
    for move in moves:
        print(refScore - move['score'], move['move'])
        if refScore - move['score'] < 250:
            N += 1

    print("N: ", N)
    i = random.randint(0, N-1)
    return moves[i]['move']


def simpleMessenger(board):

    return None

    messages = [
        "Hola, soy un robotito!",
        "Ahora seremos amigos para siempre",
        "Te parece bien?",
        None, None, None,
        "Genial!",
        None,
        "Me iban a llamar IJO, pero mi creador pensó que BOT IJO no quedaba muy bien",
        None, None,
        "Gracias por jugar conmigo",
        None, None,
        "Mi cumpleaños es el 18 de marzo, acuérdate de felicitarme",
        "Creo que @analyze es una gran jugada",
        "Pero no me hagas mucho caso"
    ]

    n = board.fullmove_number - 1

    if not board.turn and n < len(messages):

        msg = messages[n]

        if msg and "@analyze" in msg:
            move = analyze(board, searchDepth = 10)
            msg = msg.replace("@analyze", board.san(move))

        return msg


def wait_for_challenges():
    '''
      Continuously wait for challenges.
      When a challenge comes, accept it, play the game and continue.
        No input
        No output
    '''

    s = requests.Session()
    with s.get(API + 'stream/event', headers = AUTH, stream = True) as answer:

        for line in answer.iter_lines():
            if line:
                info = json.loads(line)
                print(info, flush = True)

                if info.get('type') == 'challenge':

                    gameID = info.get('challenge').get('id')
                    accept_challenge(gameID)
                    play_game(gameID, weak_engine, simpleMessenger)

                if info.get('type') == 'gameStart':

                    gameID = info.get('game').get('id')

                    if gameID == 'M1Xu7JqQ':
                        continue

                    play_game(gameID, weak_engine, simpleMessenger)
    s.close()


if __name__ == '__main__':

    try:
        user = sys.argv[1]
        gameID = challenge_user(user, increment = 0, rated = True)

        if wait_for_starting_game(gameID):
            play_game(gameID, weak_engine, simpleMessenger)

    except:
        wait_for_challenges()

    STOCKFISH.close()
