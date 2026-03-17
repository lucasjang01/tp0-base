import logging
import signal
import socket

from common.protocol import send_message, recv_message


class Client:
    def __init__(self, config):
        self._config = config
        self._conn = None

    def __handle_sigterm(self, signum, frame):
        logging.info(f"action: handle_sigterm | result: success | client_id: {self._config['id']}")
        if self._conn:
            self._conn.close()
            logging.info(f"action: close_resource | result: success | resource: connection | client_id: {self._config['id']}")
        exit(0)

    def start_client_loop(self):
        signal.signal(signal.SIGTERM, self.__handle_sigterm)

        try:
            self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host, port = self._config['server_address'].split(':')
            self._conn.connect((host, int(port)))
        except OSError as e:
            logging.critical(f"action: connect | result: fail | client_id: {self._config['id']} | error: {e}")
            return

        try:
            bet = self._config['bet']
            payload = f"{self._config['id']},{bet['nombre']},{bet['apellido']},{bet['documento']},{bet['nacimiento']},{bet['numero']}"

            send_message(self._conn, payload)

            ack = recv_message(self._conn)
            if ack == "OK":
                logging.info(f"action: apuesta_enviada | result: success | dni: {bet['documento']} | numero: {bet['numero']}")
        except OSError as e:
            logging.error(f"action: send_message | result: fail | client_id: {self._config['id']} | error: {e}")
        finally:
            self._conn.close()
            logging.info(f"action: close_resource | result: success | resource: connection | client_id: {self._config['id']}")
