"""
This file contains the Hill Myna backend source code, which is directly called by the GUI.
"""
from azure import Credentials, CredentialsManager, SpeechToTextClient, IdentificationClient
from words import WordManager
from typing import List
from audio import Audio
from users import User, UsersManager
from datetime import datetime
from collections import namedtuple
import time

"""
Represents a single identification result.
"""
IdentificationResult = namedtuple("IdentificationResult", "azure_id confidence")


class HillMyna:

    def __init__(self, data_directory: str, tmp_directory: str,
                 credentials_fn: str = "credentials.csv", words_fn: str = "words.txt", users_fn: str = "users.json",
                 speech_resource: str = "SpeechBS2019", identification_resource: str = "SpeakerBS2019",
                 operation_check_time: int = 30, remove_silences: bool = False,
                 debug: bool = False):
        """
        Hill myna backend constructor.
        :param data_directory: Path to a directory containing all the data needed to run the program
        :param tmp_directory: Path to a directory where to store temporary files (i.e. audio files)
        :param credentials_fn: Name of the file containing resource names, API keys, and REST endpoints
        :param words_fn: Name of the file containing words for anti-spoofing reasons
        :param users_fn: Name of the file containing HillMyna users
        :param speech_resource: Name of the Azure resource to be used for speech-to-text
        :param identification_resource: Name of the Azure resource to be used for speaker identification
        :param operation_check_time: Time (in seconds) to wait before querying Azure for operation result; can be tweaked to reduce API limits consume
        :param remove_silences: (EXPERIMENTAL) if True, silence is detected and removed from audio files before Azure processes it
        :param debug: if True, debug messages are printed to the standard output
        """

        assert data_directory is not None, "Data directory must be provided."
        assert tmp_directory is not None, "Temporary file directory must be provided."
        assert operation_check_time >= 0, "Invalid value for operation check time."

        self.__debug = debug
        self.tmp_directory = tmp_directory
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

    # --- General ---
    def operation_status(self, operation_id: str, enrollment: bool = False, identification: bool = True) -> (str, str):
        """
        Checks the outcome of either an enrollment or an identification operation. The two are MUTUALLY EXCLUSIVE.
        In the case of an enrollment operation: returns a string containing the status of the enrollment phase.
        In the case of an identification operation: returns a tuple of strings in the format (Azure ID, confidence).
        ATTENTION: an Azure ID equal to '00000000-0000-0000-0000-000000000000' means NO MATCH for the set of candidate IDs.
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
            self.__users_manager.remove(identifier=azure_id)

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

    def identification(self, audio_path: str, short_audio: bool = False) -> User:
        """
        Returns the User identified in the given audio file, breaking possible ties.
        :param audio_path: Path to the audio file
        :param short_audio: if True, audio can be as short as 1 second; otherwise, minimum length is 5 seconds (5 minutes max anyway)
        :return: User identified in the given audio, raises an error otherwise
        """

        ret = None

        # list of operation IDs to be checked later
        op_ids = []

        # iterate on the lists of candidates, max 10 at once
        iters = 1
        for candidates in self.__users_manager.get_all_users():
            op_ids.append(self.__SpeakerClient.new_identification(audio_path=audio_path,
                                                                  candidate_ids=candidates,
                                                                  short_audio=short_audio))

            # prevent the 20 requests in a minute limitation - 200+ users should be an edge case
            iters += 1
            if iters == 19:
                if self.__debug:
                    print("Waiting in order not to get banned for Azure API constraints.")
                time.sleep(65)
                iters = 1

        # wait for identification results
        time.sleep(self.operation_check_time)

        # check status - more than one user might be identified
        identified_users = []
        iters = 1
        for op_id in op_ids:
            azure_id, confidence = self.operation_status(operation_id=op_id)

            # prevent the 20 requests in a minute limitation - 20+ requests should be an edge case
            iters += 1
            if iters == 19:
                if self.__debug:
                    print("Waiting in order not to get banned for Azure API constraints.")
                time.sleep(65)
                iters = 1

            # if there was a match
            if azure_id != "00000000-0000-0000-0000-000000000000":
                identified_users.append(IdentificationResult(azure_id=azure_id,
                                                             confidence=confidence))

        # break ties, if any
        if len(identified_users) > 1:
            # debug stuff
            if self.__debug:
                print("Identification: there are {num} ties.".format(num=len(identified_users)))
                for result in identified_users:
                    print("\t- {user} with confidence {conf}".format(user=self.__users_manager.get_by_azure_id(azure_id=result.azure_id).username,
                                                                     conf=result.confidence))

            # still check for the 10 candidates max limit
            op_ids = []
            candidates = []
            iters = 1
            for result in identified_users:
                candidates.append(result.azure_id)

                if len(candidates) == 10:
                    op_ids.append(self.__SpeakerClient.new_identification(audio_path=audio_path,
                                                                          candidate_ids=candidates,
                                                                          short_audio=short_audio))
                    candidates = []

                    # prevent the 20 requests in a minute limitation - 200+ ties should be an EXTREME edge case
                    iters += 1
                    if iters == 19:
                        if self.__debug:
                            print("Waiting in order not to get banned for Azure API constraints.")
                        time.sleep(65)
                        iters = 1

            if len(candidates) > 0:
                op_ids.append(self.__SpeakerClient.new_identification(audio_path=audio_path,
                                                                      candidate_ids=candidates,
                                                                      short_audio=short_audio))

                # prevent the 20 requests in a minute limitation - 200+ ties should be an EXTREME edge case
                iters += 1
                if iters == 19:
                    if self.__debug:
                        print("Waiting in order not to get banned for Azure API constraints.")
                    time.sleep(65)
                    iters = 1

            # wait for identification results
            time.sleep(self.operation_check_time)

            # check status
            iters = 1
            for op_id in op_ids:
                azure_id, confidence = self.operation_status(operation_id=op_id)

                # prevent the 20 requests in a minute limitation - 20+ requests should be an EXTREME edge case
                iters += 1
                if iters == 19:
                    if self.__debug:
                        print("Waiting in order not to get banned for Azure API constraints.")
                    time.sleep(65)
                    iters = 1

                # if there was a match
                if azure_id != "00000000-0000-0000-0000-000000000000":
                    ret = IdentificationResult(azure_id=azure_id,
                                               confidence=confidence)

        # simple case, there is only 1 identified user
        elif len(identified_users) == 1:
            ret = identified_users[0]

        # retrieve user
        if ret is not None:
            user = self.__users_manager.get_by_azure_id(azure_id=ret.azure_id)
            if self.__debug:
                print("Identification: {user} with confidence {conf}".format(user=user.username,
                                                                             conf=ret.confidence))
        else:
            raise RuntimeError("No user has been identified.")

        return user

    def get_users_number(self) -> int:
        return self.__users_manager.get_users_number()

    def get_all_users(self):
        return self.__users_manager.get_all_users()

    def test(self):
        h = HillMyna(data_directory="../data", tmp_directory="../tmp", debug=True)

        # random pick words
        h.get_words()
        # do the recording and get the path
        a = datetime.utcnow()
        ts = time.mktime(a.timetuple())
        audio_path = "../tmp/audio{timestamp}.wav".format(timestamp=ts)
        a = Audio(path=audio_path, blocking=True)
        a.rec(duration=6)
        IDclient = IdentificationClient(h.__credentials_manager.get("SpeakerBS2019"))
        profileID = IDclient.new_profile()
        status_url = IDclient.new_enrollment(profileID, audio_path)
        print("PROFILE:  "+profileID)
        print("STATUS:   "+str(status_url))
        a.delete()
        #print(IDclient.operation_status(status_URL))#RuntimeError: Get operation status failed: POST responded with 404 Resource not found
        #print(IDclient.get_profile(status_URL)) #RuntimeError: Get profile failed: POST responded with 404 Resource not found

    def test2(self):
        json = self.__SpeakerClient.all_profiles()
        print(json)
        print("Before: there are {num} profiles.".format(num=len(json)))
        self.__SpeakerClient.del_all_profiles()
        json = self.__SpeakerClient.all_profiles()
        print("After: there are {num} profiles.".format(num=len(json)))

    def test3(self, new_user=False, rounds=8):
        # fetch azure_id
        azure_id = None
        if new_user:
            self.new_profile(username="emanuele", name="e", surname="g")

        usr = self.__users_manager.get_by_username(username="emanuele")
        time.sleep(self.operation_check_time)

        # enrollment
        # TODO while usr.status == self.ENROLLING --> maybe in the GUI
        for i in range(rounds):
            print("Round {i}\n".format(i=i))
            # record
            audio_path = "{base}/audio{ts}.wav".format(base=self.tmp_directory, ts=time.mktime(datetime.utcnow().timetuple()))
            audio = Audio(path=audio_path,
                          blocking=True)

            self.get_words()
            audio.rec(duration=6)

            # actual enrollment
            op_id = self.enrollment(azure_id=usr.azure_id, audio_path=audio_path)
            time.sleep(self.operation_check_time)
            result = self.operation_status(operation_id=op_id,
                                           enrollment=True,
                                           identification=False)
            print(result)
            audio.delete()

        print(self.__SpeakerClient.get_profile(profile_id=usr.azure_id))

if __name__ == "__main__":
    h = HillMyna(data_directory="../data", tmp_directory="../tmp", debug=True)
    h.test3(new_user=False, rounds=1)
