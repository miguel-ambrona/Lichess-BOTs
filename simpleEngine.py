#!/usr/bin/env python3

import random
import sys

import myBot

# Must install python-chess for the following:
import chess
import chess.engine

STOCKFISH = chess.engine.SimpleEngine.popen_uci('./Stockfish/src/stockfish')

class SimpleEngine(object):

    def __init__(self):
        '''
          SimpleEngine object creator.
        '''

        self.INFTY = 1000000

    def stockfish(self, board, searchDepth = 10, outputInfo = False, multiPV = 1):
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


    def absolute_evaluation(self, board):

        if board.is_checkmate():
            return -self.INFTY if board.turn else self.INFTY

        if board.is_stalemate():
            return 0

        sfen = board.fen().split(' ')[0]
        material = 0
        material += 100 * (sfen.count('P') - sfen.count('p'))
        material += 300 * (sfen.count('N') - sfen.count('n'))
        material += 325 * (sfen.count('B') - sfen.count('b'))
        material += 500 * (sfen.count('R') - sfen.count('r'))
        material += 910 * (sfen.count('Q') - sfen.count('q'))

        evaluation = material if board.turn else -material

        if board.is_check():
            evaluation += (-10 if board.turn else +10)

        return evaluation


    def alphabeta(self, board, depth, alpha, beta, maximizingPlayer):

#        print(board)
#        print(self.absolute_evaluation(board))
#        print()

        if depth == 0 or board.is_game_over():
            return (self.absolute_evaluation(board), None)

        best = None

        if maximizingPlayer:
            value = -self.INFTY

            for move in board.legal_moves:
                board.push(move)
                (v, ponder) = self.alphabeta(board, depth-1, alpha, beta, False)
                board.pop()

                if v >= value:
                    value = v
                    best = move

            return (value, best)

        else:
            value = +self.INFTY

            for move in board.legal_moves:
                board.push(move)
                (v, ponder) = self.alphabeta(board, depth-1, alpha, beta, True)
                board.pop()

                if v <= value:
                    value = v
                    best = move

            return (value, best)


    def analyse(self, board, depth):
        return self.alphabeta(board, depth, -self.INFTY, +self.INFTY, board.turn)


    def weak_engine(moves):
        '''
          Weak engine that picks a move
            Input:
                 board (chess.Board type, from python-chess)

            Output:
                 move (chess.Move.from_uci type, from python-chess)
        '''

        b = chess.Board()
        for move in moves.split(' '):
            b.push_uci(move)

        moves = stockfish(b, searchDepth = 10, outputInfo = True, multiPV = 9)
        refScore = moves[0]['score']

        N = 0
        for move in moves:
            print(refScore - move['score'], move['move'])
            if refScore - move['score'] < 250:
                N += 1

        print("N: ", N)
        i = random.randint(0, N-1)
        return str(moves[i]['move'])


e = SimpleEngine()
b = chess.Board('rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2')

print (e.analyse(b, 4))

STOCKFISH.close()
