import requests
from threading import Thread

URL = "URL:PORT"
ATTEMPTS = 10

if __name__ == "__main__":
    for i in range(ATTEMPTS):
        thread = Thread(target=requests.get, args=(URL,))
        thread.start()
