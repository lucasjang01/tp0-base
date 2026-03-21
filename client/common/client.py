import csv
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

        agency_id = self._config['id']
        max_amount = self._config['batch_max_amount']
        dataset_path = f"/data/agency-{agency_id}.csv"

        try:
            self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host, port = self._config['server_address'].split(':')
            self._conn.connect((host, int(port)))
        except OSError as e:
            logging.critical(f"action: connect | result: fail | client_id: {agency_id} | error: {e}")
            return

        try:
            self._send_all_bets(agency_id, max_amount, dataset_path)
            send_message(self._conn, "FIN")
            self._query_winners(agency_id)
        except OSError as e:
            logging.error(f"action: send_message | result: fail | client_id: {agency_id} | error: {e}")
        finally:
            self._conn.close()
            logging.info(f"action: close_resource | result: success | resource: connection | client_id: {agency_id}")

    def _send_all_bets(self, agency_id, max_amount, dataset_path):
        with open(dataset_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            batch = []
            for row in reader:
                nombre, apellido, documento, nacimiento, numero = row
                batch.append(f"{agency_id},{nombre},{apellido},{documento},{nacimiento},{numero}")
                if len(batch) == max_amount:
                    self._send_batch(batch)
                    batch = []
            if batch:
                self._send_batch(batch)

    def _query_winners(self, agency_id):
        send_message(self._conn, f"WINNERS {agency_id}")
        response = recv_message(self._conn)
        if response is None:
            logging.error(f"action: consulta_ganadores | result: fail | error: connection closed")
            return
        winners = [dni for dni in response.split('\n') if dni]
        logging.info(f"action: consulta_ganadores | result: success | cant_ganadores: {len(winners)}")

    def _send_batch(self, batch):
        payload = '\n'.join(batch)
        send_message(self._conn, payload)
        ack = recv_message(self._conn)
        cantidad = len(batch)
        if ack == "OK":
            logging.info(f"action: apuesta_enviada | result: success | cantidad: {cantidad}")
        else:
            logging.error(f"action: apuesta_enviada | result: fail | cantidad: {cantidad}")
