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


def stockfish(board, searchDepth = 10, outputInfo = False, multiPV = 1):
    '''
      Pick a move using Stockfish at a low depth.
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


def pp_move(board, uci_move):
    '''
      Pretty print a move.
        Input:
             board (chess.Board type, from python-chess)
              move (string: move in UCI format)

        Output:
            string (move in SAN format)
    '''
    san = board.san(chess.Move.from_uci(uci_move))
    #san = san.replace('K','♔').replace('Q','♕').replace('R','♖')
    #san = san.replace('B','♗').replace('N','♘')
    return san


def weak_engine(moves, clockSeconds, oppSeconds):
    '''
      Weak engine that picks a move.
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
         1 : "Hola, soy uno de los Robots de la Academia de Ajedrez Chamberi. 🤖", # Robot
         3 : "¡Buena partida! 🍀", # Clubs
         7 : "Por cierto, gracias por jugar conmigo.",
         9 : "Bueno, quiero decir contra mí. 😈", # Evil
        20 : "🥱", # Bored
        21 : "😜", # Kidding
    }

    msg = messages.get(b.fullmove_number, None)

    # Classify the move by the opponent according to the book
    if len(moves) > 0:
        b.pop()
        prefix = str(b.fullmove_number) + ("." if b.turn else "...")
        move_info = book.classifyMove(BOOK, b, move)

        if move_info:
            best = move_info.get('top5')

            if not move_info.get('is_good') and best:
                msg = "🧐 Tu jugada, %s, no es muy popular. Los mejores jugadores hacen %s en su lugar. 🤔" \
                    % (prefix + pp_move(b, move), pp_move(b, best[0][0]))

        b.push_uci(move)

    # Calculate the best moves
    moves = stockfish(b, searchDepth = 6, outputInfo = True, multiPV = 8)

    # Add an intentional delay

    if clockSeconds > oppSeconds and clockSeconds > 20:
        time.sleep(random.randint(5,10))

    elif clockSeconds > 60 and b.fullmove_number > 3:
        wait = min(clockSeconds / 70, 10)
        time.sleep(max(wait, 1))

    else:
        time.sleep(1)

    if b.fullmove_number < 5:
        move = book.randomBookMove(BOOK, b)
        if move:
            return move, msg

    print ("SCORE:", moves[0]['score'])

    if moves[0]['score'] < -400:
        msg = "Juegas muy bien, ¿no? 😰" # Sad

    if -500000 < moves[0]['score'] < -30000 and random.random() < 1/2:
        return 'resign', '¡Bien jugado! 🎉🥳' # Party

    okMoves = [m for m in moves if moves[0]['score'] - m['score'] < 200]

    if random.random() < 1/2:
        choice = random.choice(okMoves)

    else:
        notHorrible = [m for m in moves if moves[0]['score'] - m['score'] < 500]
        notWinning = [m for m in notHorrible if m['score'] < 100]
        if len(notWinning) > 0:
            choice = random.choice(notWinning)

        else:
            choice = random.choice(okMoves)

    return str(choice['move']), msg


if __name__ == '__main__':

    chamberiBot = myBot.Bot('ClubAjedrezChamberi', 'oaUsKX1NPwk1PyBg',
                            weak_engine, "Aquí tienes 10 segundos, ¡úsalos bien!")
    try:
        user = sys.argv[1]
        gameID = chamberiBot.challenge_user(user, rated = False)

        if chamberiBot.wait_for_starting_game(gameID):
            chamberiBot.play_game(gameID)

    except Exception:
        chamberiBot.wait_for_challenges()


STOCKFISH.close()
WEAKENGINE.close()
