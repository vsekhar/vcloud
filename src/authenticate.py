import hmac
import os
import socket

from multiprocessing.connection import AuthenticationError

MESSAGE_LENGTH = 20

CHALLENGE = b'#CHALLENGE#'
WELCOME = b'#WELCOME#'
FAILURE = b'#FAILURE#'

def deliver_challenge(socket, authkey):
	assert isinstance(authkey, bytes)
	message = os.urandom(MESSAGE_LENGTH)
	socket.sendall(CHALLENGE + message)
	digest = hmac.new(authkey, message).digest()
	response = socket.recv(256)        # reject large message
	if response == digest:
		socket.sendall(WELCOME)
	else:
		socket.sendall(FAILURE)
		raise AuthenticationError('digest received was wrong')

def answer_challenge(socket, authkey):
	assert isinstance(authkey, bytes)
	timeout = socket.gettimeout()
	socket.settimeout(1)
	try:
		message = socket.recv(256)         # reject large message
	except socket.timeout:
		raise AuthenticationError('timeout')
	assert message[:len(CHALLENGE)] == CHALLENGE, 'message = %r' % message
	message = message[len(CHALLENGE):]
	digest = hmac.new(authkey, message).digest()
	socket.sendall(digest)
	try:
		response = socket.recv(256)        # reject large message
	except socket.timeout:
		raise AuthenticationError('timeout')
	if response != WELCOME:
		raise AuthenticationError('digest sent was rejected')
	socket.settimeout(timeout)


