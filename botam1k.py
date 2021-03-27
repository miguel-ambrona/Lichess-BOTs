#!/usr/bin/env python3

import random
import sys

import myBot
import book

# Must install python-chess for the following:
import chess
import chess.engine
import chess.polyglot

STOCKFISH = chess.engine.SimpleEngine.popen_uci('./Stockfish/src/stockfish')
BOOK = chess.polyglot.open_reader("/usr/share/scid/books/elite.bin")

def stockfish(board, seconds = 1, outputInfo = False, multiPV = 1):
    '''
      Pick a move using Stockfish at a low depth
        Input:
             board (chess.Board type, from python-chess)

        Output:
             move (chess.Move.from_uci type, from python-chess)
    '''

    global STOCKFISH
    limit = chess.engine.Limit(time = seconds)

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


def botam1k(moves, clockSeconds):
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

    # Find a book move
    if b.fullmove_number < 5:
        move = book.randomBookMove(BOOK, b)
        if move:
            return move, None


    PV, seconds = (5, clockSeconds / 100)# if clockSeconds > 30 else (1, 0.1)

    # Calculate the best moves
    moves = stockfish(b, seconds = seconds, outputInfo = True, multiPV = PV)
    inTheDirt = [m for m in moves if m['score'] > 200]

    print(moves)
    print()
    print(inTheDirt)

    messages = {
         1 : "Hello, the name's ANIC, BOT AM1K!",
         5 : "I was mint to be called BOT ANIK but craetor and I have spelling porblems",
         7 : "I bury my opponents, that's why I am Botamik",
        35 : "I will checkmate you in 50 moves",
    }

    msg = messages.get(b.fullmove_number, None)
    answer = moves[0] if len(inTheDirt) == 0 or b.fullmove_number >= 70 else inTheDirt[-1]

    if not msg and random.random() < 1/3:
        if answer != moves[0]:
            good, bad = b.san(moves[0]['move']), b.san(inTheDirt[-1]['move'])
            msg1 = "You wanted me to play %s, I think %s is more fun" % (good, bad)
            msg2 = "%s was good, %s is nasty" % (good, bad)
            msg3 = "I soemtiems forget how to play"
            msg4 = "I have to make this gaem interesting"
            msg5 = "I can baet you evn after such a blunder"
            msg6 = "Alrihgt! I wheel give you some chance"

            msg = random.choice([msg1, msg2, msg3, msg4, msg5, msg6])

    return str(answer['move']), msg


if __name__ == '__main__':

    Botam1k = myBot.Bot('am1k', 'OsnjdrB8HWAEWtOv', botam1k, "Here is 10 seconds, use them wisely")

    try:
        user = sys.argv[1]
        gameID = Botam1k.challenge_user(user, rated = False)

        if Botam1k.wait_for_starting_game(gameID):
            Botam1k.play_game(gameID)

    except:
        Botam1k.wait_for_challenges()


STOCKFISH.close()
