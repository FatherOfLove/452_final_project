# coding=utf-8

import json
import logging
import random
from SocketServer import BaseRequestHandler, ThreadingTCPServer
from threading import Lock

from config import SERVER_HOST, SERVER_PORT
from protocol import AuthProtocol, MessageProtocol

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sample = random.sample(range(1, 16), 3)
result = {'round1': {}, 'round2': {}, 'round3': {}}

lock = Lock()


def find_round_winner(game_round):
    # find the round winner
    tmp = result.get(game_round)
    while 1:
        if len(tmp.keys()) == 2:
            clients = tmp.keys()
            if tmp[clients[0]] > tmp[clients[1]]:
                return clients[0]
            if tmp[clients[0]] < tmp[clients[1]]:
                return clients[1]
            if tmp[clients[0]] == tmp[clients[1]]:
                return -1
            break


def find_total_winner():
    # find the total winner
    winner = [find_round_winner('round{}'.format(x)) for x in [1, 2, 3]]
    # if the first game is draw, the score will be 1:1 or 0:0
    if -1 in winner:
        return -1
    else:
        return max(winner)


class PokerGameHandler(BaseRequestHandler):
    session_key = ''

    def receive_data(self):
        data = self.request.recv(1024)
        message = MessageProtocol.load_data(enc_message=data, session_key=self.session_key).message
        logging.debug('{0} receive data {1}'.format('server', message))
        return message

    def send_data(self, message):
        logging.debug('{0} send data {1}'.format('server', json.dumps(message)))
        message = MessageProtocol(message=message, session_key=self.session_key).dump_data()
        self.request.send(message)

    def handle(self):
        # handle client connected
        data = self.request.recv(1024)
        auth = AuthProtocol.load_data(data)
        verify = auth.verify()
        logging.debug('client {} verified'.format(auth.client))
        if verify:
            # get session_key
            self.session_key = auth.session_key
            # encrypt numbers with session_key
            self.send_data({'numbers': sample})
            for game_round in [1, 2, 3]:
                # send round_x info to client
                round_x = 'round{}'.format(game_round)
                self.send_data({'info': round_x})
                # receive number from client
                message = self.receive_data()
                # save the number to result
                with lock:
                    result.get(round_x).update({auth.client: message['number']})
                # find the round winner and notify the client
                round_winner = find_round_winner(round_x)
                if round_winner == -1:
                    round_result = 'draw'
                elif round_winner == auth.client:
                    round_result = 'you win'
                else:
                    round_result = 'you lose'
                self.send_data({'info': round_result})
            # find the total winner and notify the client
            total_winner = find_total_winner()
            if total_winner == -1:
                total_result = 'game over: draw'
            elif total_winner == auth.client:
                total_result = 'game over: you win'
            else:
                total_result = 'game over: you lose'
            self.send_data({'info': total_result})


if __name__ == '__main__':
    address = (SERVER_HOST, SERVER_PORT)
    server = ThreadingTCPServer(address, PokerGameHandler)
    server.serve_forever()
