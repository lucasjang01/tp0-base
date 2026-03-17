FROM python:3.11-slim
RUN mkdir -p /client_app
WORKDIR /client_app
COPY . .
ENTRYPOINT ["python3", "/client_app/main.py"]
