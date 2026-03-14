#!/usr/bin/env python3
"""
generar-compose.py
Genera un archivo Docker Compose con una cantidad configurable de clientes.
Uso: python3 generar-compose.py <archivo_salida> <num_clientes>
"""

import sys


NETWORK_NAME = "testing_net"
NETWORK_SUBNET = "172.25.125.0/24"
SERVER_IMAGE = "server:latest"
CLIENT_IMAGE = "client:latest"
SERVER_CONFIG_PATH = "./server/config.ini:/config.ini"
CLIENT_CONFIG_PATH = "./client/config.yaml:/config.yaml"


def build_server_service() -> dict:
    return {
        "container_name": "server",
        "image": SERVER_IMAGE,
        "entrypoint": "python3 /main.py",
        "environment": [
            "PYTHONUNBUFFERED=1",
        ],
        "volumes": [SERVER_CONFIG_PATH],
        "networks": [NETWORK_NAME],
    }


def build_client_service(client_id: int) -> dict:
    return {
        "container_name": f"client{client_id}",
        "image": CLIENT_IMAGE,
        "entrypoint": "/client",
        "environment": [
            f"CLI_ID={client_id}",
            "CLI_LOG_LEVEL=DEBUG",
        ],
        "volumes": [CLIENT_CONFIG_PATH],
        "networks": [NETWORK_NAME],
        "depends_on": ["server"],
    }


def build_compose(num_clients: int) -> dict:
    services = {"server": build_server_service()}
    for i in range(1, num_clients + 1):
        services[f"client{i}"] = build_client_service(i)

    return {
        "name": "tp0",
        "services": services,
        "networks": {
            NETWORK_NAME: {
                "ipam": {
                    "driver": "default",
                    "config": [{"subnet": NETWORK_SUBNET}],
                }
            }
        },
    }


def serialize_value(value, indent: int) -> str:
    """Recursively serialize a Python value to YAML-like string."""
    pad = "  " * indent
    if isinstance(value, dict):
        lines = []
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}:")
                lines.append(serialize_value(v, indent))
            else:
                lines.append(f"{pad}{k}: {serialize_value(v, 0)}")
        return "\n".join(lines)
    elif isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    prefix = f"{pad}- " if first else f"{pad}  "
                    first = False
                    if isinstance(v, (dict, list)):
                        lines.append(f"{prefix}{k}:")
                        lines.append(serialize_value(v, indent + 1))
                    else:
                        lines.append(f"{prefix}{k}: {serialize_value(v, 0)}")
            else:
                lines.append(f"{pad}- {item}")
        return "\n".join(lines)
    else:
        return str(value)


def write_compose(compose: dict, output_file: str) -> None:
    """Write the compose dict to a YAML file."""
    lines = []

    # name
    lines.append(f"name: {compose['name']}")
    lines.append("services:")

    for svc_name, svc in compose["services"].items():
        lines.append(f"  {svc_name}:")
        for key, val in svc.items():
            if isinstance(val, list):
                lines.append(f"    {key}:")
                for item in val:
                    lines.append(f"      - {item}")
            elif isinstance(val, dict):
                lines.append(f"    {key}:")
                for k, v in val.items():
                    lines.append(f"      {k}: {v}")
            else:
                lines.append(f"    {key}: {val}")

    lines.append("")
    lines.append("networks:")
    for net_name, net_cfg in compose["networks"].items():
        lines.append(f"  {net_name}:")
        lines.append(f"    ipam:")
        lines.append(f"      driver: {net_cfg['ipam']['driver']}")
        lines.append(f"      config:")
        for cfg in net_cfg["ipam"]["config"]:
            lines.append(f"        - subnet: {cfg['subnet']}")

    with open(output_file, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <output_file> <num_clients>")
        sys.exit(1)

    output_file = sys.argv[1]
    try:
        num_clients = int(sys.argv[2])
        if num_clients < 1:
            raise ValueError
    except ValueError:
        print("Error: num_clients must be a positive integer")
        sys.exit(1)

    compose = build_compose(num_clients)
    write_compose(compose, output_file)
    print(f"Generated {output_file} with {num_clients} client(s)")


if __name__ == "__main__":
    main()
