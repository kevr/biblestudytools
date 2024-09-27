import requests


class HttpError(Exception):
    pass


def get(uri):
    response = requests.get(uri)
    status = response.status_code
    if status != 200:
        raise HttpError(f"returned status {status}")
    return response.content
