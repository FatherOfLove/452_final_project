# coding=utf-8


import json
from base64 import b64decode, b64encode
from binascii import b2a_hex, a2b_hex

from Crypto.Cipher import DES
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA, DSA
from Crypto.Signature import DSS, pkcs1_15

from config import PLAYER_KEYS


def load_key(key_path, algorithm):
    # load private key
    with open(key_path, 'r') as keyFile:
        # read the key file
        key_content = keyFile.read()
        if algorithm == 'RSA':
            # decode the key
            decoded_key = b64decode(key_content)
            # load the key
            key = RSA.importKey(decoded_key)
        if algorithm == 'DSA':
            # decode the key
            decoded_key = b64decode(key_content)
            # load the key
            key = DSA.importKey(decoded_key)
    return key


class AuthProtocol(object):
    def __init__(self, algorithm, client, session_key, signature):
        """
        auth info
        :param algorithm: RSA or DSA
        :param client: client name
        :param session_key: session_key
        :param signature: signature to verify client identity and session_key
        """
        self.algorithm = algorithm
        self.client = client
        self.session_key = session_key
        self.signature = signature

    @classmethod
    def load_data(cls, data):
        # factory method
        # load data from string
        data = json.loads(data)
        return cls(algorithm=data['algorithm'], client=data['client'], session_key=data['session_key'],
                   signature=data['signature'])

    def dump_data(self):
        # dump data to string
        data = {'algorithm': self.algorithm, 'client': self.client, 'session_key': self.session_key,
                'signature': self.signature}
        return json.dumps(data)

    def verify(self):
        # verify the client itself and message
        # convert message to sorted string
        message = json.dumps({'client': self.client, 'session_key': self.session_key}, sort_keys=True)
        # convert signature from ascii to binary
        signature = a2b_hex(self.signature)
        # calculate the sha256 of the message
        hash_message = SHA256.new(message)
        # RSA
        if self.algorithm == 'RSA':
            # load the public key
            pub_key = load_key(PLAYER_KEYS[self.client]['RSA_PUB_KEY'], self.algorithm)
            # use public key to generate a verifier
            verifier = pkcs1_15.new(pub_key)
        # DSA
        if self.algorithm == 'DSA':
            # load the public key
            pub_key = load_key(PLAYER_KEYS[self.client]['DSA_PUB_KEY'], self.algorithm)
            # use public key to generate a verifier
            verifier = DSS.new(pub_key, 'fips-186-3')
        try:
            # verify the signature
            verifier.verify(hash_message, signature)
            return True
        except ValueError:
            return False

    def sign(self):
        # sign the message use private key
        # convert message to sorted string
        message = json.dumps({'client': self.client, 'session_key': self.session_key}, sort_keys=True)
        # calculate the sha256 of the message
        hash_message = SHA256.new(message)
        # RSA
        if self.algorithm == 'RSA':
            # load the private key
            priv_key = load_key(PLAYER_KEYS[self.client]['RSA_PRIV_KEY'], self.algorithm)
            # use private key to generate a signer
            signer = pkcs1_15.new(priv_key)
        # DSA
        if self.algorithm == 'DSA':
            # load the private key
            priv_key = load_key(PLAYER_KEYS[self.client]['DSA_PRIV_KEY'], self.algorithm)
            # use private key to generate a signer
            signer = DSS.new(priv_key, 'fips-186-3')
        # sign the message
        signature = signer.sign(hash_message)
        # convert signature from binary to ascii
        self.signature = b2a_hex(signature)


class MessageProtocol(object):
    def __init__(self, session_key, message):
        """
        encrypt and decrypt message
        :param session_key: session_key
        :param message: original message
        """
        self.session_key = session_key
        self.message = message

    def dump_data(self):
        # convert original message to encrypted message
        session_key = self.session_key.ljust(8, ' ')
        message = json.dumps(self.message, sort_keys=True)
        message = message.ljust((len(message) / 16 + 1) * 16)
        cipher = DES.new('{}'.format(session_key), DES.MODE_ECB)
        enc_message = cipher.encrypt(message)
        return b64encode(enc_message)

    @classmethod
    def load_data(cls, session_key, enc_message):
        # factory method
        # convert encrypted message to original message
        session_key = session_key.ljust(8, ' ')
        enc_message = b64decode(enc_message)
        cipher = DES.new('{}'.format(session_key), DES.MODE_ECB)
        session_key = session_key.rstrip(' ')
        message = cipher.decrypt(enc_message).rstrip(' ')
        message = json.loads(message)
        return cls(session_key=session_key, message=message)


if __name__ == '__main__':
    dsa_auth = AuthProtocol(algorithm='DSA', client='PLAYER1', session_key='abcdef', signature='')
    dsa_auth.sign()
    print dsa_auth.verify()
    rsa_auth = AuthProtocol(algorithm='RSA', client='PLAYER2', session_key='abcdef', signature='')
    rsa_auth.sign()
    print rsa_auth.verify()
    des_message = MessageProtocol(message={'key': 'value'}, session_key='abcdef')
    MessageProtocol.load_data(session_key='abcdef', enc_message=des_message.dump_data())
