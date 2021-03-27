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
            return move

    # Calculate the best moves
    moves = stockfish(b, seconds = clockSeconds / 100, outputInfo = True, multiPV = 5)
    inTheDirt = [m for m in moves if m['score'] > 200]

    print(moves)
    print()
    print(inTheDirt)

    if len(inTheDirt) and b.fullmove_number <= 70:
        print(inTheDirt[-1]['score'])
        return str(inTheDirt[-1]['move'])

    else:
        print(moves[0]['score'])
        return str(moves[0]['move'])


def botam1kMsg(moves):

    messages = [
        "Hi, I am a Bonatic!",
        None,
        "Let the luck be with you!",
        None, None, None, None, None,
        "I know you will give up very soon",
        None, None, None, None, None, None,
        "Still palying?",
    ]

    # Set the board
    b = chess.Board()
    for move in moves:
        b.push_uci(move)

    n = b.fullmove_number - 1

    if not b.turn and n < len(messages):

        msg = messages[n]

        if msg and "@analyze" in msg:
            move = stockfish(b, searchDepth = 10)
            msg = msg.replace("@analyze", b.san(move))

        return msg


if __name__ == '__main__':

    Botam1k = myBot.Bot('am1k', 'OsnjdrB8HWAEWtOv', botam1k, botam1kMsg)

    try:
        user = sys.argv[1]
        gameID = Botam1k.challenge_user(user, rated = False)

        if Botam1k.wait_for_starting_game(gameID):
            Botam1k.play_game(gameID)

    except:
        Botam1k.wait_for_challenges()


STOCKFISH.close()
