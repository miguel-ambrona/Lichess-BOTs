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

    global CHOSEN_IDX
    if len(moves) < 2:
        CHOSEN_IDX = []

    # Set the board
    b = chess.Board()
    for move in moves:
        b.push_uci(move)

    messages = {
         1 : "Hello, the name's ANIC, BOT AM1K! 🤖🌱", #Robot, plant
         5 : "I was mint to be called BOT ANIK but craetor and I have spelling porblems 🥴", # Drunken
         7 : "I bury my opponents, that's why I am Botamik ⚰️", # Coffin
        10 : "🥱", # Bored
        11 : "😴", # Asleep
        27 : "🍃", # Plants
        35 : "I will checkmate you in 50 moves 🎉🥳", # Party
        39 : "Let me pin dis game 📌 for furhter analysis 🙄", # Pin, distracted
        51 : "🦾", # Robot arm
        70 : "🥀" # Leaves falling
    }

    msg = messages.get(b.fullmove_number, None)

    # Find a book move
    move = book.randomBookMove(BOOK, b)
    if move:
        return move, msg

    PV, seconds = (5, clockSeconds / 100)# if clockSeconds > 30 else (1, 0.1)

    # Calculate the best moves
    moves = stockfish(b, seconds = seconds, outputInfo = True, multiPV = PV)
    inTheDirt = [m for m in moves if m['score'] > 200]

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
            msg2 = "%s was good, %s is nasty 🤢" % (good, bad) # Nasty
            msg3 = "I soemtiems forget how to play 🤓" # Nerd
            msg4 = "I have to make this gaem interesting ☺" # Cute
            msg5 = "I can baet you evn after such a blunder 🤯" # Head explodes
            msg6 = "Alrihgt! I wheel give you some chance 🚑" # Ambulance
            msg7 = "You zink my move was bad. This is how I woudl decrribe it: 💩" # Shit
            msg8 = "I love bludners! %s is magical! ✨" % (bad) # Sparkles

            idx = random.randint(1,8)
            if not idx in CHOSEN_IDX:
                msg = [msg1, msg2, msg3, msg4, msg5, msg6, msg7, msg8][idx-1]

            CHOSEN_IDX.append(idx)

    b.push(answer['move'])
    if b.is_checkmate():
        msg = "I am the best! 😎" # Sunglasses

    return str(answer['move']), msg


if __name__ == '__main__':

    Botam1k = myBot.Bot('am1k', 'OsnjdrB8HWAEWtOv', botam1k,
                        "Here is 10 seconds, use them wisely 🤫") # Silence

    try:
        user = sys.argv[1]
        gameID = Botam1k.challenge_user(user, rated = False)

        if Botam1k.wait_for_starting_game(gameID):
            Botam1k.play_game(gameID)

    except:
        Botam1k.wait_for_challenges()


STOCKFISH.close()
