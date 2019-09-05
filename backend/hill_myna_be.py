"""
This file contains the Hill Myna backend source code, which is directly called by the GUI.
"""
from azure import Credentials, CredentialsManager, SpeechToTextClient, IdentificationClient
from words import WordManager
from typing import List
from audio import Audio
from datetime import datetime
import time


class HillMyna:

    def __init__(self, data_directory: str, tmp_directory: str,
                 credentials_fn: str = "credentials.csv", words_fn: str = "words.txt",
                 speech_resource: str = "SpeechBS2019", identification_resource: str = "SpeakerBS2019",
                 operation_check_time: int = 30, remove_silences: bool = False,
                 debug: bool = False):
        """
        Hill myna backend constructor.
        :param data_directory: Path to a directory containing all the data needed to run the program
        :param tmp_directory: Path to a directory where to store temporary files (i.e. audio files)
        :param credentials_fn: Name of the file containing resource names, API keys, and REST endpoints
        :param words_fn: Name of the file containing words for anti-spoofing reasons
        :param speech_resource: Name of the Azure resource to be used for speech-to-text
        :param identification_resource: Name of the Azure resource to be used for speaker identification
        :param operation_check_time: Time (in seconds) to wait before querying Azure for operation result; can be tweaked to reduce API limits consume
        :param remove_silences: (EXPERIMENTAL) if True, silence is detected and removed from audio files before Azure processes it
        :param debug: if True, debug messages are printed to the standard output
        """

        assert data_directory is not None, "Data directory must be provided"
        assert tmp_directory is not None, "Temporary file directory must be provided"

        self.__debug = debug

        if self.__debug:
            print("Loading credentials file...")
        self.__credentials_manager = CredentialsManager("{base}/{filename}".format(base=data_directory,
                                                                                   filename=credentials_fn))

        if self.__debug:
            print("Loading words file...")
        self.__words_manager = WordManager(words_path="{base}/{filename}".format(base=data_directory,
                                                                                 filename=words_fn),
                                           debug=self.__debug)

        if self.__debug:
            print("Initializing speech-to-text client...")
        creds = self.__credentials_manager.get(speech_resource)
        self.__SpeechClient = SpeechToTextClient(credentials=creds, debug=self.__debug)

        if self.__debug:
            print("Initializing speaker identification client...")
        creds = self.__credentials_manager.get(identification_resource)
        self.__SpeakerClient = IdentificationClient(credentials=creds, debug=self.__debug)

    # --- General ---
    def operation_status(self, url: str, enrollment: bool = False, identification: bool = True) -> str or (str, str):
        """
        Checks the outcome of either an enrollment or an identification operation. The two are MUTUALLY EXCLUSIVE.
        In the case of an enrollment operation: returns a string containing the status of the enrollment phase.
        In the case of an identification operation: returns a tuple of strings in the format (Azure ID, confidence).
        ATTENTION: an Azure ID equal to '00000000-0000-0000-0000-000000000000' means NO MATCH for the set of candidate IDs.
        :param url: URL to query for updates, either associated to an enrollment operation, or to an identification one
        :param enrollment: if True, the operation to check is an enrollment one (MUTUALLY EXCLUSIVE, default: False)
        :param identification: if True, the operation to check is an identification one (MUTUALLY EXCLUSIVE, default: True)
        :return: string or tuple of strings (according to the operation type) encoding the status of the operation
        """

        assert not (enrollment and identification), "Enrollment and identification are two mutually exclusive operations."
        assert enrollment or identification, "An operation must be provided."

        ret = ""
        json_response = self.__SpeakerClient.operation_status(operation_id=url)     # TODO check url != operation ID
        status = json_response["status"]
        if status == "failed":
            # fetch the error message
            msg = json_response["message"]
            ret = "The operation is failed with message: {msg}.".format(msg=msg)

        elif status == "running":
            ret = "The operation is running."

        elif status == "notstarted":
            ret = "The operation is not started."

        elif status == "succeeded":
            # fetch the actual result of the operation
            json_response = json_response["processingResult"]

            # go through all the enrolment cases
            if enrollment:
                status = json_response["enrollmentStatus"]
                if status == "Enrolling":
                    # fetch the remaining time in order to complete enrollment
                    remaining_time = json_response["remainingEnrollmentSpeechTime"]
                    ret = "Enrollment phase can be completed with {time} more seconds.".format(time=remaining_time)

                elif status == "Training":
                    ret = "Profile is currently in training phase and will be soon ready for identification."

                elif status == "Enrolled":
                    ret = "Successfully enrolled."

            # go through all the identification cases
            elif identification:
                azure_id = json_response["identifiedProfileId"]     # No-match ID: "00000000-0000-0000-0000-000000000000"
                confidence = json_response["confidence"]

                ret = (azure_id, confidence)

        return ret
    # --- --- ---

    # --- Profile management ---
    # creation, deletion, enrolment, check status, list all profiles
    def new_profile(self, username: str, name: str, surname: str) -> None:
        """
        Creates a new user profile and associates a new Azure ID to it.
        :param username: User-chosen nickname
        :param name: User's first name
        :param surname: User's last name
        :return: None
        """

        assert username is not None, "Username must be provided."
        assert name is not None, "Name must be provided."
        assert surname is not None, "Surname must be provided."

        azure_id = self.__SpeakerClient.new_profile()
        # TODO user management: add user profile

    def delete_profile(self, username: str = None, azure_id: str = None) -> None:
        """
        Deletes an existing user profile, referenced either by its username or Azure ID.
        If both are provided, the referenced profile MUST be the same.
        :param username: User-chosen nickname (Optional)
        :param azure_id: Azure ID (Optional)
        :return: None
        """

        assert not (username is None and azure_id is None), "Either a username or an Azure ID must be provided."

        if username is not None and azure_id is not None:
            # TODO user management: check username and azure_id refer to the same user profile
            pass

        # TODO user management: find azure_id if only username is provided
        if self.__SpeakerClient.del_profile(profile_id=azure_id):
            # TODO user management: delete user profile
            pass

    def enrollment(self, audio_path: str, username: str = None, azure_id: str = None, short_audio: bool = False) -> str:
        """
        Associates a new enrollment procedure to an existing profile, referenced either by its username or Azure ID.
        If both are provided, the referenced profile MUST be the same.
        :param audio_path: Path to the audio file
        :param username: User-chosen nickname (Optional)
        :param azure_id: Azure ID (Optional)
        :param short_audio: if True, audio can be as short as 1 second; otherwise, 5 seconds (Optional, default: False)
        :return: URL to query for updates on this enrolment request status
        """

        assert not (username is None and azure_id is None), "Either a username or an Azure ID must be provided."

        if username is not None and azure_id is not None:
            # TODO user management: check username and azure_id refer to the same user profile
            pass

        # TODO user management: find azure_id if only username is provided
        url = self.__SpeakerClient.new_enrollment(profile_id=azure_id,
                                                  audio_path=audio_path,
                                                  short_audio=short_audio)

        return url
    # --- --- ---

    # --- Logging in ---
    # word fetching, speech-to-text operations, identification operations
    def get_words(self) -> List[str]:
        """
        Returns a list of randomly chosen words, containing no duplicates.
        :return: No-duplicate list of randomly chosen words
        """

        words = self.__words_manager.get_words()
        return words

    def speech_to_text(self, audio_path: str, detailed: bool = False) -> List[str]:
        """
        Returns a list of words recognized in the given audio file.
        :param audio_path: Path to the audio file
        :param detailed: if True, retrieves the detailed version of the Azure response
        :return: List of recognized words
        """

        ret = None

        json_response = self.__SpeechClient.recognize(audio_path=audio_path, detailed=detailed)
        if self.__debug:
            print(json_response)

        # retrieve Azure status
        status = json_response["RecognitionStatus"]
        if status == "Success":
            # retrieve recognized words as a string
            ret = json_response["NBest"][0]["Lexical"] if detailed else json_response["DisplayText"]
            ret = ret.lower().strip(".")

            # split the string by whitespace
            ret = ret.split(" ")

        elif status == "NoMatch":
            raise RuntimeError("No English word could be recognized in your recording.")

        elif status == "InitialSilenceTimeout":
            raise RuntimeError("Too much silence in the start of your recording.")

        elif status == "BabbleTimeout":
            raise RuntimeError("Too much noise in the start of your recording.")

        elif status == "Error":
            raise RuntimeError("Microsoft Azure internal error.")

        return ret
    # --- --- ---

    # --- Benchmarks ---
    # threshold tuning, spoofing attacks
    # --- --- ---


if __name__ == "__main__":
    h = HillMyna(data_directory="../data",
                 tmp_directory="../tmp",
                 debug=True)

    # random pick words
    h.get_words()

    # do the recording and get the path
    a = datetime.utcnow()
    ts = time.mktime(a.timetuple())
    audio_path = "../tmp/audio{timestamp}.wav".format(timestamp=ts)
    a = Audio(path=audio_path)
    a.rec(duration=60)
    time.sleep(10)
    a.stop()
    # Azure speech-to-text stuff
    h.speech_to_text(audio_path)
    a.delete()
    # --- --- ---
