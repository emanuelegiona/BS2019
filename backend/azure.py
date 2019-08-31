"""
This file contains source code for every Microsoft Azure interaction involved in this project.
"""
from rest_client import RESTClient, SimpleResponse
from collections import namedtuple
from datetime import datetime
import time
import os.path
import json


"""
Credentials object refers to credentials associated to a single resource.
"""
Credentials = namedtuple("Credentials", "key endpoint")


class CredentialsManager:
    """
    This class implements an Azure credentials manager, handling their loading from a CSV file and exposing methods to access them.
    """

    def __init__(self, credentials_path: str):
        """
        CredentialsManager constructor.
        :param credentials_path: Path to the credentials file, expected to be a CSV-formatted file.
        """

        if not os.path.exists(credentials_path):
            raise FileNotFoundError("{file} not found.".format(file=credentials_path))
        if not os.path.isfile(credentials_path):
            raise FileNotFoundError("{file} must be a regular file.".format(file=credentials_path))

        # create credentials dictionary for future use
        self.credentials = {}

        # read CSV file
        with open(credentials_path) as file:
            first_line = True
            for line in file:

                # skip CSV header
                if first_line:
                    first_line = False
                    continue

                line = line.strip("\n")
                line = line.split(",")

                # only process 3-token lines (resource, key, endpoint)
                if len(line) == 3:
                    resource = line[0]
                    creds = Credentials(key=line[1], endpoint=line[2])
                    self.credentials[resource] = creds

    def get(self, resource: str) -> Credentials:
        """
        Returns the Credentials object associated to the given resource, if any; otherwise, a RuntimeError is raised.
        :param resource: Azure resource name
        :return: Credentials object for the given resource
        """

        creds = self.credentials.get(resource, None)
        if creds is None:
            raise RuntimeError("Credentials not found for resource '{res}'".format(res=resource))
        return creds


class SpeechToTextClient:
    """
    This class implements an Azure client for the Speech REST API.
    """

    def __init__(self, credentials: Credentials, debug: bool = False):
        """
        SpeechToTextClient constructor.
        :param credentials: Credentials object associated to the SpeechToText resource
        :param debug: if True, debug messages are printed to the standard output
        """

        self.credentials = credentials
        self.debug = debug

        # Azure token to perform SpeechToText API requests, additionally to credentials
        self.token = None

        # used to computed token timeout, as its validity lasts 10 minutes
        self.token_timestamp = None

        # REST client to be used for all Azure requests
        self.client = RESTClient(debug=self.debug)

    def __authenticate(self) -> None:
        """
        Performs Azure authentication, retrieving a service token for subsequent requests.
        ATTENTION: currently disabled, service key MIGHT be enough.
        :return: None
        """

        trailing_url = "sts/v1.0/issueToken"
        headers = {"Ocp-Apim-Subscription-Key": self.credentials.key}
        service_url = "{endpoint}{trailer}".format(endpoint=self.credentials.endpoint,
                                                   trailer=trailing_url)

        response = self.client.post(url=service_url,
                                    headers=headers,
                                    expect_json=False)

        if response.code != 200:
            raise RuntimeError("Authentication failed: POST responded with {code} {msg}".format(code=response.code,
                                                                                                msg=response.message))
        self.token = response.content
        self.token_timestamp = time.mktime(datetime.utcnow().timetuple())

    def recognize(self, audio_path: str) -> json:
        """
        Recognizes text from a given audio file.
        :param audio_path: Path to the audio file
        :return: JSON object containing recognized text and other stats
        """

        if not os.path.exists(audio_path):
            raise FileNotFoundError("{file} not found.".format(file=audio_path))
        if not os.path.isfile(audio_path):
            raise FileNotFoundError("{file} must be a regular file.".format(file=audio_path))

        # check for token validity; authenticate if token is expired or about to
        #right_now = time.mktime(datetime.utcnow().timetuple())
        #if (self.token is None) or (9 < (right_now - self.token_timestamp) / 60):
        #    self.__authenticate()

        trailing_url = "speech/recognition/conversation/cognitiveservices/v1"
        headers = {"Ocp-Apim-Subscription-Key": self.credentials.key,
                   #"Authorization": "Bearer {token}".format(token=self.token),
                   "Content-type": "audio/wav; codecs=audio/pcm; samplerate=16000",
                   "Accept": "application/json"}
        parameters = {"language": "en-US",
                      "format": "simple"}   # detailed also returns confidence score

        service_url = "{endpoint}{trailer}".format(endpoint=self.credentials.endpoint,
                                                   trailer=trailing_url)

        # stream audio file content to the Azure service URL
        with open(audio_path, "rb") as file:
            response = self.client.post(url=service_url,
                                        headers=headers,
                                        params=parameters,
                                        data=file)

        if response.code != 200:
            raise RuntimeError("Recognition failed: POST responded with {code} {msg}".format(code=response.code,
                                                                                             msg=response.message))

        return response.content


class IdentificationClient:
    """
    This class implements an Azure client for the Speaker Recognition REST API regarding the identification task.
    """
    pass


if __name__ == "__main__":
    a = datetime.utcnow()
    print(a)
    a = time.mktime(a.timetuple())
    print(a)

    time.sleep(65)

    b = datetime.utcnow()
    print(b)
    b = time.mktime(b.timetuple())
    print(b)

    print((b-a)/60)
