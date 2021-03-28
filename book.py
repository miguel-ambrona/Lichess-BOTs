#!/usr/bin/env python3

import sys
import os
import json
import socket
import chess
import chess.polyglot
import random
import math

def myround(n):

    output = str(round(100*n)/100)
    if output == "100.0":  return "100"
    return output


def round_percentages(percentages,ndecimals):

    percentages_copy = percentages[:]
    percentages = [p for p in percentages if p > 0]
    scale = 10**ndecimals
    floors = [math.floor(scale*p) for p in percentages]
    decimals = [(percentages[i] - floors[i], i) for i in range(len(percentages))]
    missing = 100*scale - sum(floors)
    for (p,i) in sorted(decimals, reverse = True):
        if missing <= 0:  break
        floors[i] += 1
        missing -= 1

    output = []
    i = 0
    for p in percentages_copy:
        if p > 0:
            output.append(floors[i]/scale)
            i += 1
        else:
            output.append(0)

    return output


def learnInfo(info, min_elo = 2200):

    avg_ELO = min_elo + info.learn % 2**10
    defeats_127 = (info.learn >> 10) % 2**7
    victories_127 = (info.learn >> 17) % 2**7
    draws_127 = max(0, 127 - victories_127 - defeats_127)
    scaleFactor = (info.learn >> 24) % 2**8
    percentages = round_percentages([victories_127*100/127, draws_127*100/127, defeats_127*100/127], 2)

    if (info.weight > 0):
        halfpoints = info.weight * scaleFactor
        if victories_127 - defeats_127 > 0:
            ngames = round(halfpoints / (1 + victories_127/127 - defeats_127/127))
        else:
            ngames = 2 * halfpoints

    else:
        ngames = scaleFactor

    return info.move, ngames, ','.join([str(p) for p in percentages]), avg_ELO


def bookMoves(book, board):

    moves = {}
    N = 0
    for entry in book.find_all(board):
        m, ngames, percentages, avgELO = learnInfo(entry)
        N += ngames
        (white, draw, black) = percentages.split(',')
        moves[board.uci(m)] = {
            'UCI' : str(m),
            'SAN' : board.san(m),
            'numGames' : ngames,
            'results' : { 'white' : float(white), 'draw' : float(draw), 'black' : float(black) },
            'avgELO' : avgELO
        }
    return moves, N


def randomBookMove(book, board):

    moves, N = bookMoves(book, board)

    if N == 0:
        return None

    frequencies = [v['numGames'] for v in moves.values()]

    return random.choices(
        population = [k for k in moves.keys()],
        weights = [f/N for f in frequencies],
        k=1
    )[0]


'''
  A book move is considered good if is the most played or it has been played in
  more than 3% of the games (and at least 30 times) or it has been played in
  more than 30% of the games.
  Also we require that the move be in the Top 10 most played.
'''

def is_good(N,n,r):
    return (r == 1 or (n > 0.03 * N and N >= 30) or n > 0.3 * N) and r <= 10


def findBookMoves(book, board):

    bookmoves, N = bookMoves(book, board)
    moves = [(d['numGames'],k, d) for (k,d) in bookmoves.items()]
    moves.sort(reverse = True)
    moves = [(m,d) for (n,m,d) in moves]

    return (bookmoves, N, moves)


def top(bookmoves, N, moves, k = None):

    ms = [m for (m,d) in moves]
    top = []
    for m in moves[:k]:
        mInfo = bookmoves.get(m[0])
        if mInfo:
            n = mInfo.get('numGames')
            r = ms.index(m[0]) + 1
            if is_good(N,n,r):
                top.append(m)

    return top


'''
 If the book does not include the position of board, return None
 Otherwise, return a dictionary including:
   * numGames : number of times the game has been played in the book
   * ranking  : n if it is the n-th most played move in the position
   * is_good  : bool indicating whether the move is considered 'good'
   * top5     : list of top 5 most played moves (or fewer),
                in uci notation, most common goes first
'''

def classifyMove(book, board, move):

    (bookmoves, N, moves) = findBookMoves(book, board)

    if N == 0:
        return None

    moveInfo = bookmoves.get(move)
    output = {}

    if moveInfo:
        n = moveInfo.get('numGames')
        r = [m[0] for m in moves].index(move) + 1
        output['num_games'] = n
        output['ranking'] = r
        output['is_good'] = is_good(N,n,r)

    else:
        output['num_games'] = 0
        output['ranking'] = 0
        output['is_good'] = False

    output['top5'] = top(bookmoves, N, moves, k = 5)

    return output
