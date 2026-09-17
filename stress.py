import requests
from threading import Thread

url = "10.191.195.149:5001"

if __name__ == "__main__":
    while True:
        thread = Thread(target=requests.get, args=(url,))
        thread.start()
