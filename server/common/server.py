import logging
import signal
import socket
import threading

from common.protocol import recv_message, send_message
from common.utils import Bet, load_bets, store_bets, has_won

# Protocol message identifiers
MSG_FIN = "FIN"
MSG_WINNERS_PREFIX = "WINNERS "


class Server:
    def __init__(self, port, listen_backlog, agencies):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._running = True
        signal.signal(signal.SIGTERM, self.__handle_sigterm)

        # Barrier waits for all agencies to finish sending bets before the draw
        self._lottery_barrier = threading.Barrier(agencies)
        # Lock protects store_bets (not thread-safe per utils.py comment)
        self._store_lock = threading.Lock()

    def __handle_sigterm(self, signum, frame):
        logging.info("action: handle_sigterm | result: in_progress")
        self._running = False
        self._server_socket.close()
        logging.info("action: close_resource | result: success | resource: server_socket")
        logging.info("action: handle_sigterm | result: success")

    def run(self):
        threads = []
        while self._running:
            try:
                client_sock = self.__accept_new_connection()
                t = threading.Thread(
                    target=self.__handle_client_connection,
                    args=(client_sock,),
                    daemon=True,
                )
                t.start()
                threads.append(t)
            except OSError:
                if not self._running:
                    break
                raise

        for t in threads:
            t.join()

    def __handle_client_connection(self, client_sock):
        try:
            self.__receive_bets(client_sock)
            self.__wait_for_lottery()
            self.__answer_winners_query(client_sock)
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def __receive_bets(self, client_sock):
        """Receive bet batches until the client sends FIN."""
        while True:
            msg = recv_message(client_sock)
            if msg is None or msg == MSG_FIN:
                break
            rows = msg.strip().split('\n')
            bets = []
            try:
                for row in rows:
                    agency, first_name, last_name, document, birthdate, number = row.split(',')
                    bets.append(Bet(agency, first_name, last_name, document, birthdate, number))
                with self._store_lock:
                    store_bets(bets)
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                send_message(client_sock, "OK")
            except Exception as e:
                logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)} | error: {e}')
                send_message(client_sock, "ERROR")

    def __wait_for_lottery(self):
        """Block until all agencies have finished uploading bets, then run the draw."""
        # The first thread to arrive after all others blocks; the last one triggers the log
        index = self._lottery_barrier.wait()
        if index == 0:
            logging.info("action: sorteo | result: success")

    def __answer_winners_query(self, client_sock):
        """Read a WINNERS <agency> request and reply with the winning DNIs."""
        msg = recv_message(client_sock)
        if msg is None or not msg.startswith(MSG_WINNERS_PREFIX):
            logging.error(f"action: consulta_ganadores | result: fail | error: unexpected message")
            return

        agency_id = int(msg[len(MSG_WINNERS_PREFIX):].strip())
        winners = [
            bet.document
            for bet in load_bets()
            if bet.agency == agency_id and has_won(bet)
        ]
        payload = "\n".join(winners)
        send_message(client_sock, payload)

    def __accept_new_connection(self):
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
