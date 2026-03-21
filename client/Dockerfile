FROM python:3.11-slim
RUN pip install pyyaml --no-cache-dir
RUN mkdir -p /client_app
WORKDIR /client_app
COPY client/ .
ENTRYPOINT ["python3", "/client_app/main.py"]
