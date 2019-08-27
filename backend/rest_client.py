"""
This file contains source code for handling all the REST requests involved in this project.
"""
from collections import namedtuple
import requests
from requests.exceptions import RequestException
from json.decoder import JSONDecodeError

SimpleResponse = namedtuple("SimpleResponse", "content message")


class Client:
    """
    REST client implementing the HTTP methods that are required in order to work with Microsoft Azure.
    This wrapper class doesn't target any specific Azure service.
    """

    def __init__(self, debug=False):
        self.__debug = debug

    def get(self, url, headers=None, params=None, expect_json=True):
        content = None
        msg = ""
        try:
            req = requests.get(url=url,
                               headers=headers,
                               params=params)

            if self.__debug:
                print("GET {url} responded with {code}: {msg}".format(url=req.url,
                                                                      code=req.status_code,
                                                                      msg=req.reason))

            # fetch JSON in case it is expected one, otherwise retrieve response body as a string
            content = req.json() if expect_json else str(req.text)
            req.close()
        except JSONDecodeError:
            content = None
            msg = "Not a JSON"
        except ConnectionError:
            content = None
            msg = "Connection error"
        except TimeoutError:
            content = None
            msg = "Timeout"
        except RequestException:
            content = None
            msg = "General error"

        return SimpleResponse(content=content, message=msg)

    def post(self, url, body, headers=None, params=None):
        req = requests.post(url=url,
                            headers=headers,
                            params=params,
                            json=body)

        if self.__debug:
            print("POST {url} responded with {code}: {msg}".format(url=req.url,
                                                                   code=req.status_code,
                                                                   msg=req.reason))

        req.close()

    def delete(self, url, headers, params):
        req = requests.delete(url=url,
                              headers=headers,
                              params=params)

        if self.__debug:
            print("DELETE {url} responded with {code}: {msg}".format(url=req.url,
                                                                     code=req.status_code,
                                                                     msg=req.reason))

        req.close()


if __name__ == "__main__":
    c = Client(debug=True)
    j = c.get(url="http://httpbin.org/get")
    print(j)
