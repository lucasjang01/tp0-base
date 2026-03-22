import logging
import signal
import socket
import multiprocessing

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

        # Barrier and Lock must come from multiprocessing to work across processes
        self._lottery_barrier = multiprocessing.Barrier(agencies)
        self._store_lock = multiprocessing.Lock()

    def __handle_sigterm(self, signum, frame):
        logging.info("action: handle_sigterm | result: in_progress")
        self._running = False
        self._server_socket.close()
        logging.info("action: close_resource | result: success | resource: server_socket")
        logging.info("action: handle_sigterm | result: success")

    def run(self):
        processes = []
        while self._running:
            try:
                client_sock = self.__accept_new_connection()
                fd = client_sock.fileno()
                p = multiprocessing.Process(
                    target=_handle_client_connection,
                    args=(fd, self._lottery_barrier, self._store_lock),
                    daemon=True,
                )
                p.start()
                client_sock.close()
                processes.append(p)
            except OSError:
                if not self._running:
                    break
                raise

        for p in processes:
            p.join()


def _handle_client_connection(fd, lottery_barrier, store_lock):
    """Top-level function (required by multiprocessing) that handles one client."""
    client_sock = socket.socket(fileno=fd)
    try:
        _receive_bets(client_sock, store_lock)
        _wait_for_lottery(lottery_barrier)
        _answer_winners_query(client_sock)
    except OSError as e:
        logging.error(f"action: receive_message | result: fail | error: {e}")
    finally:
        client_sock.close()


def _receive_bets(client_sock, store_lock):
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
            with store_lock:
                store_bets(bets)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            send_message(client_sock, "OK")
        except Exception as e:
            logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)} | error: {e}')
            send_message(client_sock, "ERROR")


def _wait_for_lottery(lottery_barrier):
    index = lottery_barrier.wait()
    if index == 0:
        logging.info("action: sorteo | result: success")


def _answer_winners_query(client_sock):
    msg = recv_message(client_sock)
    if msg is None or not msg.startswith(MSG_WINNERS_PREFIX):
        logging.error("action: consulta_ganadores | result: fail | error: unexpected message")
        return

    agency_id = int(msg[len(MSG_WINNERS_PREFIX):].strip())
    winners = [
        bet.document
        for bet in load_bets()
        if bet.agency == agency_id and has_won(bet)
    ]
    payload = "\n".join(winners)
    send_message(client_sock, payload)
