"""
This file contains the Hill Myna backend source code, which is directly called by the GUI.
"""
from azure import Credentials, CredentialsManager, SpeechToTextClient, IdentificationClient


class HillMyna:

    def __init__(self, data_directory: str, tmp_directory: str,
                 credentials_fn: str = "credentials.csv",
                 speech_resource: str = "SpeechBS2019", identification_resource: str = "SpeakerBS2019",
                 operation_check_time: int = 30, remove_silences: bool = False,
                 debug: bool = False):
        """
        Hill myna backend constructor.
        :param data_directory: Path to a directory containing all the data needed to run the program
        :param tmp_directory: Path to a directory where to store temporary files (i.e. audio files)
        :param credentials_fn: Name of the file containing resource names, API keys, and REST endpoints
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
    # --- --- ---

    # --- Benchmarks ---
    # threshold tuning, spoofing attacks
    # --- --- ---
