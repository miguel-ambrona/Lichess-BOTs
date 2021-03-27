#!/usr/bin/env python3

import random
import sys
import time
from subprocess import Popen, PIPE, STDOUT

import myBot
import book

# Must install python-chess for the following:
import chess
import chess.engine
import chess.polyglot

STOCKFISH = chess.engine.SimpleEngine.popen_uci('./Stockfish/src/stockfish')
BOOK = chess.polyglot.open_reader("/usr/share/scid/books/elite.bin")
WEAKENGINE = Popen(["./weak-chess-engine/src/engine"], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
WEAKENGINE.stdout.readline()

def stockfish(board, searchDepth = 10, outputInfo = False, multiPV = 1):
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

def weak_engine(moves, clockSeconds):
    '''
      Weak engine that picks a move
        Input:
             board (chess.Board type, from python-chess)

        Output:
             move (chess.Move.from_uci type, from python-chess)
    '''

    # Set the board
    b = chess.Board()
    for move in moves:
        b.push_uci(move)

    messages = {
         1 : "Hola, soy uno de los Robots de la Academia de Ajedrez Chamberi.",
         3 : "¡Buena partida!",
         7 : "Por cierto, gracias por jugar conmigo."
    }

    msg = messages.get(b.fullmove_number, None)

    # Calculate the best moves
    moves = stockfish(b, searchDepth = 9, outputInfo = True, multiPV = 10)
    notHorrible = [m for m in moves if moves[0]['score'] - m['score'] < 500]

    if b.fullmove_number < 5:
        move = book.randomBookMove(BOOK, b)
        if move:
            time.sleep(random.randint(0,3))
            return move, msg

    print ("SCORE:", moves[0]['score'])

    if -500000 < moves[0]['score'] < -900 and random.random() < 1/2:
        return 'resign', msg

    # If there is only one non-horrible move, play it immediately with some probability
    if len(notHorrible) == 1 and random.random() < 2/3:
        return str(notHorrible[0]['move']), msg

    okMoves = [m for m in notHorrible if moves[0]['score'] - m['score'] < 200]
    # Make one of the okMoves with certain probability:
    if random.random() < 1/2:
        return str(random.choice(okMoves)['move']), msg

    # Call our weak engine on depth 4 or 5:
    depth = 2
    cmd = ("%d %s\n" % (depth, b.fen())).encode("utf-8")
    WEAKENGINE.stdin.write(cmd)
    WEAKENGINE.stdin.flush()
    output = WEAKENGINE.stdout.readline().strip().decode("utf-8")

    wait = random.randint(0, min(5, len(notHorrible)))
    if clockSeconds > 60:
        time.sleep(wait)

    if output not in [str(m['move']) for m in notHorrible]:
        print("Our move was horrible", output)
        print(okMoves)
        return str(okMoves[-1]['move']), msg

    return output, msg


if __name__ == '__main__':

    chamberiBot = myBot.Bot('ClubAjedrezChamberi', 'oaUsKX1NPwk1PyBg',
                            weak_engine, "Aquí tienes 10 segundos, ¡úsalos bien!")

    try:
        user = sys.argv[1]
        gameID = chamberiBot.challenge_user(user, rated = False)

        if chamberiBot.wait_for_starting_game(gameID):
            chamberiBot.play_game(gameID)

    except:
        chamberiBot.wait_for_challenges()


STOCKFISH.close()
WEAKENGINE.close()
