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

CHOSEN_IDX = []
SUDDEN = False
SUDDEN2 = False

def stockfish(board, seconds = 1, Depth = None, outputInfo = False, multiPV = 1):
    '''
      Pick a move using Stockfish at a low depth
        Input:
             board (chess.Board type, from python-chess)

        Output:
             move (chess.Move.from_uci type, from python-chess)
    '''

    global STOCKFISH
    if not Depth:
        limit = chess.engine.Limit(time = seconds)

    else:
        limit = chess.engine.Limit(depth = Depth)

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


def botam1k(moves, clockSeconds, oppSeconds):
    '''
      Weak engine that picks a move
        Input:
             board (chess.Board type, from python-chess)

        Output:
             move (chess.Move.from_uci type, from python-chess)
    '''

    global CHOSEN_IDX
    global SUDDEN
    global SUDDEN2
    if len(moves) < 2:
        CHOSEN_IDX = []
        SUDDEN = False
        SUDDEN2 = False

    # Set the board
    b = chess.Board()
    for move in moves:
        b.push_uci(move)

    messages = {
         1 : "Hello, the name's ANIC, BOT AM1K!",
         5 : "I was mint to be called BOT ANIK but craetor and I have spelling porblems 🥴", # Drunken
         7 : "I bury my opponents, that's why I am Botamik",
        11 : "😴", # Asleep
        35 : "I will checkmate you in 50 moves",
        39 : "Let me pin dis game 📌 for furhter analysis 🙄", # Pin, distracted
    }

    msg = messages.get(b.fullmove_number, None)

    # Find a book move
    move = book.randomBookMove(BOOK, b)
    if move:
        return move, msg

    PV, seconds = (5, clockSeconds / 100)# if clockSeconds > 30 else (1, 0.1)

    if clockSeconds > 30:

        # Calculate the best moves
        moves = stockfish(b, seconds = seconds, outputInfo = True, multiPV = PV)
        inTheDirt = [m for m in moves if m['score'] > 200]

    else:

        moves = stockfish(b, Depth = 10, outputInfo = True)
        moves = [moves]
        inTheDirt = [moves[0]]

    print(moves)
    print()
    print(inTheDirt)

    answer = moves[0] if len(inTheDirt) == 0 or b.fullmove_number >= 70 else inTheDirt[-1]

    if not msg:
        if answer != moves[0]:
            prefix = str(b.fullmove_number) + ("." if b.turn else "...")
            good = prefix + b.san(moves[0]['move'])
            bad  = prefix + b.san(inTheDirt[-1]['move'])
            msg1 = "You wanted me to play %s, I think %s is more fun 🤪" % (good, bad) # Crazy
            msg2 = "%s was good, %s is nasty" % (good, bad)
            msg3 = "I soemtiems forget how to play"
            msg4 = "I have to make this gaem interesting"
            msg5 = "I can baet you evn after such a blunder"
            msg6 = "Alrihgt! I'll give you some chance"
            msg7 = "I love bludners! %s is magical!" % (bad)

            idx = random.randint(1,7)
            if not idx in CHOSEN_IDX:
                msg = [msg1, msg2, msg3, msg4, msg5, msg6, msg7][idx-1]

            CHOSEN_IDX.append(idx)

    b.push(answer['move'])
    if b.is_checkmate():
        msg = "I am the best! 😎" # Sunglasses

    if clockSeconds < 30 and not SUDDEN:
        SUDDEN = True
        msg = "I waz playing with you like a cat with the food"

    if clockSeconds < 30 and SUDDEN and not SUDDEN2:
        SUDDEN2 = True
        msg = "No more jokes!!!"

    return str(answer['move']), msg


if __name__ == '__main__':

    Botam1k = myBot.Bot('am1k', 'OsnjdrB8HWAEWtOv', botam1k,
                        "Here is 10 seconds, use them wisely")

    try:
        user = sys.argv[1]
        gameID = Botam1k.challenge_user(user, rated = False)

        if Botam1k.wait_for_starting_game(gameID):
            Botam1k.play_game(gameID)

    except:
        Botam1k.wait_for_challenges()


STOCKFISH.close()
