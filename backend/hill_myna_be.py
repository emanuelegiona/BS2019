"""
This file contains the Hill Myna backend source code, which is directly called by the GUI.
"""
from azure import Credentials, CredentialsManager, SpeechToTextClient, IdentificationClient
from words import WordManager
from typing import List
from audio import audio
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

    # --- Profile management ---
    # creation, deletion, enrolment, check status, list all profiles
    # --- --- ---

    # --- Logging in ---
    # word fetching, speech-to-text operations, identification operations
    def get_words(self) -> List[str]:
        words = self.__words_manager.get_words()
        return words

    def speech_to_text(self, audio_path: str):
        json_response = self.__SpeechClient.recognize(audio_path=audio_path, detailed=True)
        print(json_response)
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
    a = audio()
    a.rec(duration=6, path=audio_path, block=True)

    # Azure speech-to-text stuff
    h.speech_to_text(audio_path)
    # --- --- ---
