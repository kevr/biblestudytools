import requests
from lxml import etree


class HttpError(Exception):
    pass


def parse(content: str) -> etree._Element:
    """Return lxml.etree root node of content"""
    parser = etree.HTMLParser(recover=True)
    return etree.fromstring(content, parser)


def get(uri, **kwargs):
    response = requests.get(uri, **kwargs)
    status = response.status_code
    if status != 200:
        raise HttpError(f"returned status {status}")
    return response.content
