"""
This file contains source code for every Microsoft Azure interaction involved in this project.
"""
from backend.rest_client import RESTClient
from collections import namedtuple
from typing import List
import os.path
import json
import re
import time


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
        self.__debug = debug

        # REST client to be used for all Azure requests
        self.client = RESTClient(debug=self.__debug)

    def recognize(self, audio_path: str, detailed: bool = False) -> json:
        """
        Recognizes text from a given audio file.
        :param audio_path: Path to the audio file
        :param detailed: if True, retrieves the detailed version of the Azure response
        :return: JSON object containing recognized text and other stats
        """

        if not os.path.exists(audio_path):
            raise FileNotFoundError("{file} not found.".format(file=audio_path))
        if not os.path.isfile(audio_path):
            raise FileNotFoundError("{file} must be a regular file.".format(file=audio_path))

        trailing_url = "speech/recognition/conversation/cognitiveservices/v1"
        headers = {"Ocp-Apim-Subscription-Key": self.credentials.key,
                   "Content-type": "audio/wav; codecs=audio/pcm; samplerate=16000",
                   "Accept": "application/json"}
        parameters = {"language": "en-US",
                      "format": "detailed" if detailed else "simple"}   # detailed also returns confidence score

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

    def __init__(self, credentials: Credentials, debug: bool = False):
        """
        IdentificationClient constructor.
        :param credentials: Credentials object associated to the Identification resource
        :param debug: if True, debug messages are printed to the standard output
        """

        self.credentials = credentials
        self.__debug = debug

        # REST client to be used for all Azure requests
        self.client = RESTClient(debug=self.__debug)

        self.operation_id_regex = re.compile("^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$")

    def is_valid(self, operation_id: str) -> bool:
        """
        Returns True in case the given Azure operation ID is a valid one, False otherwise.
        :param operation_id: Operation ID to check
        :return: True if operation_id is a valid Azure operation ID, False otherwise
        """

        return self.operation_id_regex.fullmatch(operation_id) is not None

    # --- profile management ---
    def new_profile(self) -> str:
        """
        Creates a new profile for identification purposes.
        :return: Azure profile ID in case of success, raises an error otherwise
        """

        trailing_url = "identificationProfiles"
        headers = {"Ocp-Apim-Subscription-Key": self.credentials.key,
                   "Content-Type": "application/json"}
        service_url = "{endpoint}{trailer}".format(endpoint=self.credentials.endpoint,
                                                   trailer=trailing_url)
        body = {"locale": "en-US"}

        response = self.client.post(url=service_url,
                                    headers=headers,
                                    body=body)
        if response.code != 200:
            msg = response.content["error"]["message"]
            raise RuntimeError("New profile failed: POST responded with {code} {msg}".format(code=response.code,
                                                                                             msg=msg))

        profile_id = response.content["identificationProfileId"]
        if self.__debug:
            print("Profile ID: {id}".format(id=profile_id))

        return profile_id

    def del_profile(self, profile_id: str) -> bool:
        """
        Deletes the profile associated to the given profile ID.
        :param profile_id: Azure profile ID
        :return: True in case of success, raises an error otherwise
        """

        trailing_url = "identificationProfiles/{id}".format(id=profile_id)
        headers = {"Ocp-Apim-Subscription-Key": self.credentials.key}
        service_url = "{endpoint}{trailer}".format(endpoint=self.credentials.endpoint,
                                                   trailer=trailing_url)

        response = self.client.delete(url=service_url,
                                      headers=headers)

        if response.code != 200:
            msg = response.content["error"]["message"]
            raise RuntimeError("Delete profile failed: POST responded with {code} {msg}".format(code=response.code,
                                                                                                msg=msg))

        return True

    def new_enrollment(self, profile_id: str, audio_path: str, short_audio: bool = False) -> str:
        """
        Creates a new enrollment request for the given profile with the given audio file.
        :param profile_id: Azure profile ID
        :param audio_path: Path to the audio file
        :param short_audio: if True, audio can be as short as 1 second; otherwise, minimum length is 5 seconds (5 minuts max anyway)
        :return: Azure operation ID assigned to this enrolment request, raises an error otherwise
        """

        if not os.path.exists(audio_path):
            raise FileNotFoundError("{file} not found.".format(file=audio_path))
        if not os.path.isfile(audio_path):
            raise FileNotFoundError("{file} must be a regular file.".format(file=audio_path))

        trailing_url = "identificationProfiles/{id}/enroll".format(id=profile_id)
        headers = {"Ocp-Apim-Subscription-Key": self.credentials.key,
                   "Content-Type": "multipart/form-data"}
        parameters = {"shortAudio": short_audio}
        service_url = "{endpoint}{trailer}".format(endpoint=self.credentials.endpoint,
                                                   trailer=trailing_url)

        with open(audio_path, "rb") as file:
            response = self.client.post(url=service_url,
                                        headers=headers,
                                        params=parameters,
                                        data=file,
                                        response_headers=True,
                                        expect_json=False)

        if response.code != 202:
            msg = response.content["error"]["message"]
            raise RuntimeError("Enrollment failed: POST responded with {code} {msg}".format(code=response.code,
                                                                                            msg=msg))

        enrolment_url = response.headers["Operation-Location"]
        if self.__debug:
            print("Enrollment URL: {url}".format(url=enrolment_url))

        return enrolment_url.split("/")[-1]

    def reset_enrollments(self, profile_id: str) -> bool:
        """
        Resets all the enrollments performed on the given profile, setting its status back to "Enrolling".
        :param profile_id: Azure profile ID
        :return: True in case of success, raises an error otherwise
        """

        trailing_url = "identificationProfiles/{id}/reset".format(id=profile_id)
        headers = {"Ocp-Apim-Subscription-Key": self.credentials.key}
        service_url = "{endpoint}{trailer}".format(endpoint=self.credentials.endpoint,
                                                   trailer=trailing_url)

        response = self.client.post(url=service_url,
                                    headers=headers)

        if response.code != 200:
            msg = response.content["error"]["message"]
            raise RuntimeError("Reset enrollments failed: POST responded with {code} {msg}".format(code=response.code,
                                                                                                   msg=msg))

        return True

    def get_profile(self, profile_id: str) -> json:
        """
        Returns the status and some stats of the given profile.
        :param profile_id: Azure profile ID
        :return: JSON in case of success, raises an error otherwise
        """

        trailing_url = "identificationProfiles/{id}".format(id=profile_id)
        headers = {"Ocp-Apim-Subscription-Key": self.credentials.key}
        service_url = "{endpoint}{trailer}".format(endpoint=self.credentials.endpoint,
                                                   trailer=trailing_url)

        response = self.client.get(url=service_url,
                                   headers=headers)

        if response.code != 200:
            msg = response.content["error"]["message"]
            raise RuntimeError("Get profile failed: POST responded with {code} {msg}".format(code=response.code,
                                                                                             msg=msg))

        return response.content

    def all_profiles(self) -> json:
        """
        Gets status and stats for all the registered profiles.
        :return: JSON in case of success, raises an error otherwise
        """

        trailing_url = "identificationProfiles"
        headers = {"Ocp-Apim-Subscription-Key": self.credentials.key}
        service_url = "{endpoint}{trailer}".format(endpoint=self.credentials.endpoint,
                                                   trailer=trailing_url)

        response = self.client.get(url=service_url,
                                   headers=headers)

        if response.code != 200:
            msg = response.content["error"]["message"]
            raise RuntimeError("Get all profiles failed: POST responded with {code} {msg}".format(code=response.code,
                                                                                                  msg=msg))

        return response.content

    def del_all_profiles(self) -> bool:
        """
        Deletes all the profiles for this Azure subscription key.
        :return: True in case of success, raises an error otherwise
        """

        all_profiles = self.all_profiles()
        iters = 1
        for profile in all_profiles:
            profile_id = profile["identificationProfileId"]
            self.del_profile(profile_id=profile_id)

            # prevent the 20 requests in a minute limitation - 20+ requests should be an EXTREME edge case
            iters += 1
            if iters == 19:
                if self.__debug:
                    print("Waiting in order not to get banned for Azure API constraints.")
                time.sleep(65)
                iters = 1

        return True

    # --- identification ---
    def new_identification(self, audio_path: str, candidate_ids: List[str], short_audio: bool = False) -> str:
        """
        Creates a new request to identify a profile among the given candidates for the given audio file.
        :param audio_path: Path to the audio file
        :param candidate_ids: List of candidate Azure profile IDs
        :param short_audio: if True, audio can be as short as 1 second; otherwise, minimum length is 5 seconds (5 minutes max anyway)
        :return: Azure operation ID assigned to this identification request, raises an error otherwise
        """

        if not os.path.exists(audio_path):
            raise FileNotFoundError("{file} not found.".format(file=audio_path))
        if not os.path.isfile(audio_path):
            raise FileNotFoundError("{file} must be a regular file.".format(file=audio_path))
        if len(candidate_ids) > 10:
            raise RuntimeError("Candidate IDs list must not exceed the size of 10.")

        trailing_url = "identify"
        headers = {"Ocp-Apim-Subscription-Key": self.credentials.key,
                   "Content-Type": "application/octet-stream"}
        parameters = {"identificationProfileIds": ",".join(candidate_ids),
                      "shortAudio": short_audio}
        service_url = "{endpoint}{trailer}".format(endpoint=self.credentials.endpoint,
                                                   trailer=trailing_url)

        with open(audio_path, "rb") as file:
            response = self.client.post(url=service_url,
                                        headers=headers,
                                        params=parameters,
                                        data=file,
                                        response_headers=True,
                                        expect_json=False)

        if response.code != 202:
            msg = response.content["error"]["message"]
            raise RuntimeError("Enrolment failed: POST responded with {code} {msg}".format(code=response.code,
                                                                                           msg=msg))

        identification_url = response.headers["Operation-Location"]
        if self.__debug:
            print("Identification URL: {url}".format(url=identification_url))

        return identification_url.split("/")[-1]

    # --- operations management ---
    def operation_status(self, operation_id: str) -> json:
        """
        Returns status of the given operation.
        :param operation_id: Azure operation ID
        :return: JSON containing the status in case of success, raises an error otherwise
        """

        assert operation_id is not None, "An operation ID must be provided."
        assert self.is_valid(operation_id), "The provided operation ID is not valid."

        trailing_url = "operations/{id}".format(id=operation_id)
        headers = {"Ocp-Apim-Subscription-Key": self.credentials.key}
        service_url = "{endpoint}{trailer}".format(endpoint=self.credentials.endpoint,
                                                   trailer=trailing_url)

        response = self.client.get(url=service_url,
                                   headers=headers)
        if response.code != 200:
            msg = response.content["error"]["message"]
            raise RuntimeError("Get operation status failed: POST responded with {code} {msg}".format(code=response.code,
                                                                                                      msg=msg))

        return response.content


if __name__ == "__main__":
    op_url = "https://speakerbs2019.cognitiveservices.azure.com/spid/v1.0/operations/258a16aa-0a3a-4e1a-bec3-2d766fda504b"
    op_id = op_url.split("/")[-1]
    print(op_id)

    r = re.compile("^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$")

    m = r.fullmatch(op_id)
    print(m)

    m = r.fullmatch("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa".replace("a", "z"))
    print(m)
