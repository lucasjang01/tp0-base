import socket
import logging
import signal

from common.protocol import recv_message, send_message
from common.utils import Bet, store_bets


class Server:
    def __init__(self, port, listen_backlog):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._running = True
        signal.signal(signal.SIGTERM, self.__handle_sigterm)

    def __handle_sigterm(self, signum, frame):
        logging.info("action: handle_sigterm | result: in_progress")
        self._running = False
        self._server_socket.close()
        logging.info("action: close_resource | result: success | resource: server_socket")
        logging.info("action: handle_sigterm | result: success")

    def run(self):
        while self._running:
            try:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
            except OSError:
                if not self._running:
                    break
                raise

    def __handle_client_connection(self, client_sock):
        try:
            while True:
                msg = recv_message(client_sock)
                if not msg:
                    break
                rows = msg.strip().split('\n')
                bets = []
                try:
                    for row in rows:
                        agency, first_name, last_name, document, birthdate, number = row.split(',')
                        bets.append(Bet(agency, first_name, last_name, document, birthdate, number))
                    store_bets(bets)
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                    send_message(client_sock, "OK")
                except Exception as e:
                    logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)} | error: {e}')
                    send_message(client_sock, "ERROR")
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def __accept_new_connection(self):
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
