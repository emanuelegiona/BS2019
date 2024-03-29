"""
This file contains the Hill Myna backend source code, which is directly called by the GUI.
"""
from backend.azure import CredentialsManager, SpeechToTextClient, IdentificationClient
from backend.words import WordManager
from typing import List
from backend.audio import Audio
from backend.users import User, UsersManager
from datetime import datetime
from collections import namedtuple
import time

"""
Represents a single identification result.
"""
IdentificationResult = namedtuple("IdentificationResult", "user confidence")


class HillMyna:
    """
    Class implementing the HillMyna backend library, in order to build GUI or CLI applications.
    """

    def __init__(self, data_directory: str, tmp_directory: str,
                 credentials_fn: str = "credentials.csv", words_fn: str = "words.txt",
                 users_fn: str = "users.json", enrollment_fn: str = "enrollment.txt",
                 speech_resource: str = "SpeechBS2019", identification_resource: str = "SpeakerBS2019",
                 word_threshold: int = 6, confidence_threshold: str = "High",
                 operation_check_time: int = 30, remove_silences: bool = False,
                 debug: bool = False):
        """
        Hill myna backend constructor.
        :param data_directory: Path to a directory containing all the data needed to run the program
        :param tmp_directory: Path to a directory where to store temporary files (i.e. audio files)
        :param credentials_fn: Name of the file containing resource names, API keys, and REST endpoints
        :param words_fn: Name of the file containing words for anti-spoofing reasons
        :param users_fn: Name of the file containing HillMyna users
        :param enrollment_fn: Name of the file containing text to be used for the enrollment operation
        :param speech_resource: Name of the Azure resource to be used for speech-to-text
        :param identification_resource: Name of the Azure resource to be used for speaker identification
        :param word_threshold: Number of minimum recognied words for a successful login
        :param operation_check_time: Time (in seconds) to wait before querying Azure for operation result; can be tweaked to reduce API limits consume
        :param remove_silences: (EXPERIMENTAL) if True, silence is detected and removed from audio files before Azure processes it
        :param debug: if True, debug messages are printed to the standard output
        """

        assert data_directory is not None, "Data directory must be provided."
        assert tmp_directory is not None, "Temporary file directory must be provided."
        assert operation_check_time >= 0, "Invalid value for operation check time."

        self.__debug = debug
        self.data_directory = data_directory
        self.tmp_directory = tmp_directory
        self.enrollment_fn = enrollment_fn
        self.word_threshold = word_threshold
        self.confidence_threshold = confidence_threshold
        self.operation_check_time = operation_check_time

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
            print("Loading users file...")
        self.__users_manager = UsersManager(users_path="{base}/{filename}".format(base=data_directory,
                                                                                  filename=users_fn))

        if self.__debug:
            print("Initializing speech-to-text client...")
        creds = self.__credentials_manager.get(speech_resource)
        self.__SpeechClient = SpeechToTextClient(credentials=creds, debug=self.__debug)

        if self.__debug:
            print("Initializing speaker identification client...")
        creds = self.__credentials_manager.get(identification_resource)
        self.__SpeakerClient = IdentificationClient(credentials=creds, debug=self.__debug)

        # profile status constants
        self.ENROLLING = "Enrolling"
        self.TRAINING = "Training"
        self.ENROLLED = "Enrolled"

        # identification contants
        self.NO_IDENTIFICATION = "00000000-0000-0000-0000-000000000000"
        self.CONFIDENCE_HIGH = "High"
        self.CONFIDENCE_NORMAL = "Normal"
        self.CONFIDENCE_LOW = "Low"

    # --- General ---
    def operation_status(self, operation_id: str, enrollment: bool = False, identification: bool = True) -> (str, str):
        """
        Checks the outcome of either an enrollment or an identification operation. The two are MUTUALLY EXCLUSIVE.
        In the case of an enrollment operation: returns a string containing the status of the enrollment phase.
        In the case of an identification operation: returns a tuple of strings in the format (Azure ID, confidence).
        :param operation_id: Azure operation ID associated either to an enrollment operation, or to an identification one
        :param enrollment: if True, the operation to check is an enrollment one (MUTUALLY EXCLUSIVE, default: False)
        :param identification: if True, the operation to check is an identification one (MUTUALLY EXCLUSIVE, default: True)
        :return: tuple of strings (according to the operation type) encoding the status of the operation
        """

        assert not (enrollment and identification), "Enrollment and identification are two mutually exclusive operations."
        assert enrollment or identification, "An operation must be provided."

        ret = ""
        json_response = self.__SpeakerClient.operation_status(operation_id=operation_id)
        status = json_response["status"]
        if status == "failed":
            # fetch the error message
            msg = json_response["message"]
            ret = ("failed", "The operation is failed with message: {msg}.".format(msg=msg))

        elif status == "running":
            ret = ("running", "The operation is running.")

        elif status == "notstarted":
            ret = ("notstarted", "The operation is not started.")

        elif status == "succeeded":
            # fetch the actual result of the operation
            json_response = json_response["processingResult"]

            # go through all the enrolment cases
            if enrollment:
                status = json_response["enrollmentStatus"]
                if status == self.ENROLLING:
                    # fetch the remaining time in order to complete enrollment
                    remaining_time = json_response["remainingEnrollmentSpeechTime"]
                    ret = (self.ENROLLING, "Enrollment phase can be completed with {time} more seconds.".format(time=remaining_time))

                elif status == self.TRAINING:
                    ret = (self.TRAINING, "Profile is currently in training phase and will be soon ready for identification.")

                elif status == self.ENROLLED:
                    ret = (self.ENROLLED, "Successfully enrolled.")

            # go through all the identification cases
            elif identification:
                azure_id = json_response["identifiedProfileId"]
                confidence = json_response["confidence"]

                ret = (azure_id, confidence)

        return ret

    def get_tmp_filename(self, prefix: str, suffix: str, auto_full_path: bool = True) -> str:
        """
        Returns a temporary filename based on the current timestamp.
        :param prefix: Filename prefix, before the timestamp
        :param suffix: Filename suffix, after the timestamp (i.e. extension - with the dot)
        :param auto_full_path: if True, the returned filename is automatically resolved to a path relative to the temporary directory
        :return: Temporary filename according to the parameters
        """

        filename = "{prefix}{ts}{suffix}".format(prefix=prefix,
                                                 ts=time.mktime(datetime.utcnow().timetuple()),
                                                 suffix=suffix)

        if auto_full_path:
            filename = "{base}/{fn}".format(base=self.tmp_directory,
                                            fn=filename)

        return filename

    @staticmethod
    def start_recording(audio_path: str, duration: int, blocking: bool = False) -> Audio:
        """
        Returns an Audio object and starts a recording operation.
        :param audio_path: Path to the audio file
        :param duration: Duration of the recording (in seconds)
        :param blocking: if True, the recording operation is blocking
        :return: Audio object referring to the active recording operation
        """

        audio = Audio(path=audio_path, blocking=blocking)
        audio.rec(duration=duration)

        return audio

    def check_confidence(self, confidence: str) -> bool:
        """
        Returns whether the confidence threshold is met or not.
        :param confidence: Confidence level of an identification, as returned by Azure
        :return: True if the given confidence meets the confidence threshold, False otherwise
        """

        if self.confidence_threshold == self.CONFIDENCE_HIGH:
            return confidence == self.CONFIDENCE_HIGH
        elif self.confidence_threshold == self.CONFIDENCE_NORMAL:
            return confidence == self.CONFIDENCE_NORMAL or confidence == self.CONFIDENCE_HIGH
        else:
            return confidence != self.CONFIDENCE_LOW
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
        # user management: add user profile
        self.__users_manager.add(azure_id=azure_id,
                                 username=username,
                                 name=name,
                                 surname=surname,
                                 status=self.ENROLLING)

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
            user_by_username = self.__users_manager.get_by_username(username=username)
            user_by_azure_id = self.__users_manager.get_by_azure_id(azure_id=azure_id)
            assert user_by_azure_id.azure_id == user_by_username.azure_id, "Azure ID and username MUST refer to the same user profile, when both provided."

        # user management: find azure_id if only username is provided
        elif username is not None:
            azure_id = self.__users_manager.get_by_username(username=username).azure_id

        if self.__SpeakerClient.del_profile(profile_id=azure_id):
            # user management: delete user profile
            self.__users_manager.remove(azure_id=azure_id)

    def delete_all_profiles(self) -> None:
        """
        Deletes all the registered profiles both on Azure and in the JSON file.
        :return: None
        """

        self.__SpeakerClient.del_all_profiles()
        for users in self.__users_manager.get_all_users():
            for user in users:
                self.__users_manager.remove(azure_id=user.azure_id)

    def enrollment(self, audio_path: str, username: str = None, azure_id: str = None, short_audio: bool = False) -> str:
        """
        Associates a new enrollment procedure to an existing profile, referenced either by its username or Azure ID.
        If both are provided, the referenced profile MUST be the same.
        :param audio_path: Path to the audio file
        :param username: User-chosen nickname (Optional)
        :param azure_id: Azure ID (Optional)
        :param short_audio: if True, audio can be as short as 1 second; otherwise, 5 seconds (Optional, default: False)
        :return: Azure operation ID assigned to this enrolment request status
        """

        assert not (username is None and azure_id is None), "Either a username or an Azure ID must be provided."

        if username is not None and azure_id is not None:
            user_by_username = self.__users_manager.get_by_username(username=username)
            user_by_azure_id = self.__users_manager.get_by_azure_id(azure_id=azure_id)
            assert user_by_azure_id.azure_id == user_by_username.azure_id, "Azure ID and username MUST refer to the same user profile, when both provided."

        # user management: find azure_id if only username is provided
        elif username is not None:
            azure_id = self.__users_manager.get_by_username(username=username).azure_id

        op_id = self.__SpeakerClient.new_enrollment(profile_id=azure_id,
                                                    audio_path=audio_path,
                                                    short_audio=short_audio)

        return op_id
    # --- --- ---

    # --- Logging in ---
    # word fetching, speech-to-text operations, identification operations
    def get_words(self, number: int = 5) -> List[str]:
        """
        Returns a list of randomly chosen words, containing no duplicates.
        :param number: Number of words to be sampled from the dictionary
        :return: No-duplicate list of randomly chosen words
        """

        words = self.__words_manager.get_words(number=number)
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

    def __identification(self, audio_path: str, candidates: List[str], short_audio: bool = False) -> IdentificationResult or None:
        """
        Returns an IdentificationResult containing the identified User and the confidence in case of success, None otherwise.
        :param audio_path: Path to the audio file
        :param candidates: List of Azure IDs representing the candidates for this identification procedure
        :param short_audio: if True, audio can be as short as 1 second; otherwise, minimum length is 5 seconds (5 minutes max anyway)
        :return: IdentificationResult in case of successful identification, None otherwise
        """

        # perform identification
        op_id = self.__SpeakerClient.new_identification(audio_path=audio_path,
                                                        candidate_ids=candidates,
                                                        short_audio=short_audio)

        # wait for identification results
        time.sleep(self.operation_check_time)

        # check status
        azure_id, confidence = self.operation_status(operation_id=op_id)
        if self.__debug:
            print("Azure ID: {azure_id} - Confidence: {conf}".format(azure_id=azure_id, conf=confidence))

        if self.__SpeakerClient.is_valid(operation_id=azure_id):
            if azure_id != self.NO_IDENTIFICATION and self.check_confidence(confidence=confidence):
                return IdentificationResult(user=self.__users_manager.get_by_azure_id(azure_id=azure_id),
                                            confidence=confidence)
            else:
                return None

        # in the case the result is NOT a valid Azure ID, it means that the returned tuple is actually (status, message) encoding the error
        else:
            raise RuntimeError("Identification status: {status} - {msg}".format(status=azure_id,
                                                                                msg=confidence))

    def identification(self, audio_path: str, all_users: List[List[User]] = None, short_audio: bool = False, iteration: int = 1) -> User or None:
        """
        Returns the identified User in case of successful identification, None otherwise.
        :param audio_path: Path to the audio file
        :param all_users: List of lists, each containing at most 10 User objects
        :param short_audio: if True, audio can be as short as 1 second; otherwise, minimum length is 5 seconds (5 minutes max anyway)
        :param iteration: Number of iterations reached by the identification procedure, in case of ties
        :return: Identified User, or None in case of identification failure
        """

        if all_users is None:
            all_users = self.__users_manager.get_all_users()

            # balance out the last identification request not to have only 1 candidate (if possible)
            if len(all_users) > 1 and len(all_users[-1]) == 1:
                all_users[-1].append(all_users[-2].pop())

        # iterate on user lists of size at most 10
        identified_users = []
        iters = 1
        if self.__debug:
            print("Performing identification (iteration {num})...".format(num=iteration))

        for candidates in all_users:
            result = self.__identification(audio_path=audio_path,
                                           candidates=[c.azure_id for c in candidates],
                                           short_audio=short_audio)

            if result is not None and result.user.azure_id != self.NO_IDENTIFICATION:
                identified_users.append(result.user)

                if self.__debug:
                    print("\t- {user} with confidence {conf}".format(user=result.user.username,
                                                                     conf=result.confidence))

            # enforce API constraints
            iters += 1
            if iters == 9:
                if self.__debug:
                    print("Waiting in order not to get banned for Azure API constraints.")
                time.sleep(65)
                iters = 1

        if self.__debug:
            print("Done.")

        # in case no user could be identified
        if len(identified_users) == 0:
            return None

        # there has been a single identified user - should be the norm
        elif len(identified_users) == 1:
            return identified_users[0]

        # recursively break ties, if multiple users have been identified
        else:
            user = self.identification(audio_path=audio_path,
                                       all_users=[identified_users],
                                       short_audio=short_audio,
                                       iteration=iteration + 1)

            return user

    def get_users_number(self) -> int:
        """
        Proxy method for UsersManager.
        :return: Total number of users
        """

        return self.__users_manager.get_users_number()

    def get_all_users(self):
        """
        Proxy method for UsersManager.
        :return: List of lists, each containing at most 10 User objects
        """

        return self.__users_manager.get_all_users()

    def get_by_username(self, username:str) -> User:
        return self.__users_manager.get_by_username(username)

    def update_status(self, azure_id: str, new_status: str) -> None:
        """
        Updates a user status with the given one.
        :param azure_id: Azure ID referring to the user
        :param new_status: New status message
        :return: None
        """
        self.__users_manager.update_status(azure_id, new_status)

    # --- Testing methods ---
    def test_enrollment(self, username: str):
        """
        Long text enrollment test
        :param username: Username of the user to create
        :return: None
        """

        self.new_profile(username=username,
                         name="aaa",
                         surname="bbb")
        usr = self.__users_manager.get_by_username(username=username)
        audio_path = self.get_tmp_filename(prefix="audio",
                                           suffix=".wav")

        with open("{base}/{fn}".format(base=self.data_directory,
                                       fn=self.enrollment_fn)) as f:
            for line in f:
                print(line.strip("\n"))

        audio = self.start_recording(audio_path=audio_path,
                                     duration=60,
                                     blocking=True)
        op_id = self.enrollment(azure_id=usr.azure_id,
                                audio_path=audio_path)
        time.sleep(self.operation_check_time)
        result = self.operation_status(operation_id=op_id,
                                       enrollment=True,
                                       identification=False)
        print(result)
        audio.delete()
        print(self.__SpeakerClient.get_profile(profile_id=usr.azure_id))

    def test_identification(self):
        """
        Identification test on all registered profiles
        :return: None
        """

        audio_path = self.get_tmp_filename(prefix="audio",
                                           suffix=".wav")
        self.get_words(number=10)
        audio = self.start_recording(audio_path=audio_path,
                                     duration=20)
        time.sleep(15)
        audio.stop()
        user = self.identification(audio_path=audio_path,
                                   short_audio=True)
        audio.delete()
        print("\nIdentified user: {u}".format(u=user))
    # --- --- ---


if __name__ == "__main__":
    h = HillMyna(data_directory="../data", tmp_directory="../tmp", debug=True)
    h.delete_all_profiles()
