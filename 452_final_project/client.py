# coding=utf-8
import json
import logging
import random
import socket
import string

from config import SERVER_HOST, SERVER_PORT
from protocol import AuthProtocol, MessageProtocol

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Client(object):
    def __init__(self, name, algorithm):
        """
        init client
        :param name: client name
        :param algorithm: digital signature algorithm
        """
        self.name = name
        self.algorithm = algorithm
        self.session_key = ''
        self.address = address = (SERVER_HOST, SERVER_PORT)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(self.address)

    def gen_session_key(self):
        # generate session key
        self.session_key = ''.join(random.sample(string.ascii_letters + string.digits, 8))

    def verify(self):
        # sign the message and send to the server
        self.gen_session_key()
        auth = AuthProtocol(algorithm=self.algorithm, client=self.name, session_key=self.session_key, signature='')
        auth.sign()
        message = auth.dump_data()
        self.client.sendall(message)

    def receive_data(self):
        # receive the message from the server
        data = self.client.recv(1024)
        message = MessageProtocol.load_data(enc_message=data, session_key=self.session_key).message
        logging.debug('{0} receive data {1}'.format(self.name, message))
        return message

    def send_data(self, message):
        # send the message to the server
        logging.debug('{0} send data {1}'.format(self.name, json.dumps(message)))
        message = MessageProtocol(message=message, session_key=self.session_key).dump_data()
        self.client.send(message)

    def run_game(self):
        # run the game
        message = self.receive_data()
        numbers = message['numbers']
        print numbers
        for game_round in [1, 2, 3]:
            round_x = self.receive_data()
            print round_x['info']
            while 1:
                number = raw_input('input number: ')
                number = int(number)
                if number in numbers:
                    numbers.remove(number)
                    break
                else:
                    print 'invalid input:'.format(number)
                    print 'you CANNOT choose the same number, please choose again!!! {}'
            self.send_data({'number': number})
            round_winner = self.receive_data()
            print round_winner['info']
        game_winner = self.receive_data()
        print game_winner['info']


if __name__ == '__main__':
    name = raw_input('client name [PLAYER1/PLAYER2]: ')
    algorithm = raw_input('digital signature algorithm [RSA/DSA]: ')
    client = Client(name, algorithm)
    client.verify()
    client.run_game()
