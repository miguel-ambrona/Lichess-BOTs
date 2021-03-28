#!/usr/bin/env python3

import requests
import json
import time


class Bot(object):

    def __init__(self, name, token, moveSelector, addTimeMessage):
        '''
          Bot object creator.
            Input:
                      name (string: BOT name)
                     token (string: AUTH2 token)
             moveoSelector (function that takes a string list of game moves (UCI format)
                            and outputs a possible next move (UCI format))
             chatMessenger (function that takes a string list of game moves (UCI format)
                            and outputs a string (chat text to be sent))
        '''

        self.name  = name
        self.token = token
        self.api   = 'https://lichess.org/api/'
        self.auth  = { 'Authorization': 'Bearer ' + token }

        self.moveSelector  = moveSelector
        self.addTimeMessage = addTimeMessage


    def __str__(self):
        return "BOT %s with AUTH TOKEN %s" % (self.name, self.token[:3] + "..." + self.token[-3:])


    def challenge_user(self, username, rated = False, seconds = 180, inc = 0):
        '''
          Challenge a user to a game.
            Input:
                 username (name of the user to be challenged)
                    rated (optional, Boolean indicating whether the game is rated)
                  seconds (optional, clock initial time in seconds)
                      inc (optional, clock increment in seconds)

            Output:
                   gameID (challenge identifier, which will be the game identifier if accepted)
        '''
        params = { 'rated': str(rated).lower(), 'clock.limit': seconds,
                   'clock.increment': inc }
        ans = requests.post(self.api + 'challenge/' + username, headers = self.auth, data = params)
        info = json.loads(ans.text)
        return info['challenge']['id']


    def cancel_challenge(self, gameID):
        '''
          Cancel a challenge.
            Input:
                 gameID (challenge identifier)
        '''
        requests.post(self.api + 'challenge/' + gameID + '/cancel', headers = self.auth)


    def accept_challenge(self, gameID):
        '''
          Accept a challenge.
            Input:
                 gameID (challenge identifier)
        '''
        requests.post(self.api + 'challenge/' + gameID + '/accept', headers = self.auth)


    def resign_game(self, gameID):
        '''
          Resign a game.
            Input:
                 gameID (game identifier)
        '''
        requests.post(self.api + 'bot/game/' + gameID + '/resign', headers = self.auth)


    def abort_game(self, gameID):
        '''
          Abort a game.
            Input:
                 gameID (game identifier)
        '''
        requests.post(self.api + 'bot/game/' + gameID + '/abort', headers = self.auth)


    def add_time(self, gameID, seconds):
        '''
          Add time to the opponent clock.
            Input:
                 gameID (game identifier)
                seconds (int: seconds to be add)
        '''
        requests.post(self.api + 'round/' + gameID + '/add-time/' + str(seconds), headers = self.auth)


    def wait_for_starting_game(self, gameID):
        '''
          Execute this after having sent a challenge has been created with 'challenge_user'.
            Input:
                 gameID (resulting from the challenge_user call).

            Output:
                Boolean (true) if the challenge was accepted, (false) if it was aborted
        '''
        s = requests.Session()
        with s.get(self.api + 'stream/event', headers = self.auth, stream = True) as ans:

            counter = 0
            for line in ans.iter_lines():

                # If the challenge has not been accepted after 3 cycles, cancel it
                counter += 1
                if counter >= 3:
                    self.cancel_challenge(gameID)
                    s.close()
                    return False

                if line:
                    info = json.loads(line)

                if info.get('type') == 'gameStart' and info.get('game').get('id') == gameID:
                    s.close()
                    return True

                elif info.get('type') == 'challengeDeclined' and \
                     info.get('challenge').get('id') == gameID:
                    s.close()
                    return False

        s.close()
        return False


    def play_game(self, gameID):
        '''
          Play a game which has started.
            Input:
                    gameID (game identifier)
        '''
        s = requests.Session()

        addedTime = False
        with s.get(self.api + 'bot/game/stream/' + gameID,
                   headers = self.auth, stream = True) as ans:

            for line in ans.iter_lines():
                if line:
                    print(line, flush = True)
                    info = json.loads(line)
                    state = info.get('state')

                    # Check if we got a message from the chat and continue in that case
                    if info.get('type') == 'chatLine':
                        continue

                    if state:

                        # Get the color our BOT is playing with
                        botIsWhite = info.get('white').get('id') == self.name.lower()

                        # Check if we need to abort the game cause the opponent did not move
                        if time.time() * 1000 - info.get('createdAt') > 60 * 1000: # 1 minute
                            self.abort_game(gameID)

                    else:
                        state = info

                    # If the game is finished, terminate
                    if state.get('status') != 'started':
                        s.close()
                        return

                    movesStr = state.get('moves', '')
                    moves = [] if len(movesStr) == 0 else movesStr.split(' ')

                    # Continue the loop if it is not the BOT's turn
                    if (1 if botIsWhite else 0) == len(moves) % 2:
                        continue

                    # Pick a move using the moveSelector
                    clockMS = state.get('wtime') if botIsWhite else state.get('btime')
                    m, msg = self.moveSelector(moves, clockMS / 1000)

                    # Possibly write in the chat
                    if msg:
                        params1 = { 'room' : 'player', 'text' : msg }
                        params2 = { 'room' : 'spectator', 'text' : msg }
                        requests.post(self.api + 'bot/game/' + gameID + '/chat',
                                      headers = self.auth, data = params1)
                        requests.post(self.api + 'bot/game/' + gameID + '/chat',
                                      headers = self.auth, data = params2)

                    if m == 'resign':
                        self.resign_game(gameID)
                        break

                    opponentMS = state.get('btime') if botIsWhite else state.get('wtime')
                    if (opponentMS / 1000 < 15) and (clockMS / 1000 > 30):
                        self.add_time(gameID, 10)
                        if not addedTime:
                            params1 = { 'room' : 'player', 'text' : self.addTimeMessage }
                            params2 = { 'room' : 'spectator', 'text' : self.addTimeMessage }
                            requests.post(self.api + 'bot/game/' + gameID + '/chat',
                                          headers = self.auth, data = params1)
                            requests.post(self.api + 'bot/game/' + gameID + '/chat',
                                          headers = self.auth, data = params2)
                        addedTime = True

                    requests.post(self.api + 'bot/game/' + gameID + '/move/' + m,
                                  headers = self.auth)

        s.close()


    def wait_for_challenges(self):
        '''
          Continuously wait for challenges.
          When a challenge comes, accept it, play the game and continue.
        '''
        s = requests.Session()
        with s.get(self.api + 'stream/event', headers = self.auth, stream = True) as ans:

            for line in ans.iter_lines():
                if line:
                    info = json.loads(line)
                    print(info, flush = True)

                    if info.get('type') == 'challenge':

                        gameID = info.get('challenge').get('id')

                        if info.get('challenge').get('variant').get('key') != 'standard':
                            continue

                        self.accept_challenge(gameID)
                        self.play_game(gameID)

                    if info.get('type') == 'gameStart':

                        gameID = info.get('game').get('id')

                        if gameID == 'M1Xu7JqQ':
                            continue

                        self.play_game(gameID)
        s.close()
