"""
This file contains source code for starting the GUI of Hill Myna.
"""
from appJar.appjar import ItemLookupError
from backend.hill_myna_be import HillMyna
from appJar import gui
import time
from backend.audio import Audio
from datetime import datetime


class HillMynaGUI:
    """
    Class implementing HillMyna GUI.
    """

    def __init__(self, debug: bool = False):
        """
        HillMyna GUI constructor.
        :param debug: if True, debug messages are printed to the standard output
        """

        self.__backend = HillMyna(data_directory="data",
                                  tmp_directory="tmp",
                                  debug=debug)

        self.__debug = debug
        self.__main_window = gui()
        self._row_number = None
        self.add_tabs()
        self.__main_window.setTitle("Hill Myna")
        self.__main_window.setSize(700, 500)
        self.__main_window.setResizable(True)

    # --- Main window ---
    def add_tabs(self, main_window: bool = True) -> None:
        """
        Builds the main window and the tab structure.
        :param main_window: if True, the main window is being built
        :return: None
        """

        self.__main_window.startTabbedFrame("MainWindow")

        # --- main login form ---
        self.__main_window.startTab("Login")

        self.__main_window.addLabel("Welcome to Hill Myna!")

        if main_window:
            self.__main_window.addLabel("Click on the button to start login procedure.")
            self.__main_window.addButton("login", func=self.login_function)
        else:
            self.__main_window.addLabel("Logging in...")
        self.__main_window.stopTab()
        # --- --- ---

        # --- user management form ---
        self.__main_window.startTab("Users")
        self.show_db()
        self.__main_window.stopTab()
        if self.__backend.get_users_number() == 0:
            self.__main_window.setTabbedFrameSelectedTab("MainWindow", "Users")
            self.__main_window.setTabbedFrameDisabledTab("MainWindow", "Login")
        # --- --- ---
        self.__main_window.stopTabbedFrame()
    # --- --- ---

    # --- Identification phase ---
    def login_function(self) -> None:
        """
        Implements the login button, setting the main window in login mode.
        :return: None
        """

        if self.__debug:
            print("Logging in...")
        self.__main_window.openTab("MainWindow", "Login")
        self.__main_window.emptyCurrentContainer()
        self.__display_words = self.__backend.get_words(number=10)
        words = ""
        for word in self.__display_words:
            words += "- "+word+"\n"
        self.__main_window.message("Repeat", "Whenever you're ready, click rec and repeat the following terms:\n\n" + words)
        self.__main_window.addNamedButton("rec", "identification_rec", self.rec_identification)
        self.__main_window.stopTab()

    def logout_function(self) -> None:
        """
        Implements the logout function, restoring the main window as when it first starts.
        :return: None
        """

        self.__main_window.openTab("MainWindow", "Login")
        self.__main_window.emptyCurrentContainer()
        self.__main_window.addLabel("Click on the button to start login procedure.")
        self.__main_window.addButton("login", func=self.login_function)
        self.__main_window.stopTab()

    def rec_identification(self, btn):
        """
        Implements the identification task, comprising both the speech-to-text and the user identification phases.
        :param btn: (unused)
        :return: None
        """

        if self.__main_window.getButton("identification_rec") == "rec":
            audio_path = "{base}/audio{ts}.wav".format(base=self.__backend.tmp_directory,
                                                       ts=time.mktime(datetime.utcnow().timetuple()))
            self.__audio = self.__backend.start_recording(audio_path, duration=60)
            self.__main_window.setButton("identification_rec", "stop")
        elif self.__main_window.getButton("identification_rec") == "stop":
            self.__audio.stop()
            try:
                self.__main_window.openTab("MainWindow", "Login")
                self.__main_window.emptyCurrentContainer()
                self.__main_window.addMessage(title="identification_status", text="Recognizing words...")
                if self.__debug:
                    print("Recognizing words...")
                recognized_words = set(self.__backend.speech_to_text(self.__audio.path))
                if self.__debug:
                    print("Expected: {w}".format(w=self.__display_words))
                    print("Recognized: {w}".format(w=recognized_words))
                intersection = recognized_words.intersection(set(self.__display_words))
                if self.__debug:
                    print("Correctly recognized {n} words: {w}".format(n=len(intersection), w=intersection))
                user = None
                if len(recognized_words.intersection(set(self.__display_words))) >= self.__backend.word_threshold:
                    self.__main_window.setMessage(title="identification_status", text="Identifying user...")
                    if self.__debug:
                        print("Identifying user...")
                    selected_users = [self.__backend.get_by_username(username="angelo"),
                                      self.__backend.get_by_username(username="emanuele"),
                                      self.__backend.get_by_username(username="matteo")]
                    user = self.__backend.identification(self.__audio.path, all_users=[selected_users], short_audio=True)
                    if user is not None:
                        self.__main_window.setMessage(title="identification_status", text="Logged in as {user}".format(user=str(user.username)))
                    else:
                        self.__main_window.setMessage(title="identification_status", text="No user could be identified.")
                else:
                    self.__main_window.setMessage(title="identification_status",
                                                  text="Too few words have been recognized ({n} instead of {t}).".format(n=len(intersection),
                                                                                                                         t=self.__backend.word_threshold))
                self.__main_window.addButton("Logout" if user is not None else "Try again", func=self.logout_function)
                self.__audio.delete()
            except Exception as e:
                self.__audio.delete()
                self.__main_window.errorBox("Error:", str(e))
    # --- --- ---

    # --- User management ---
    def show_new_profile_form(self) -> None:
        """
        Implements the new user window.
        :return: None
        """

        try:
            self.__main_window.startSubWindow("New profile")
            self.__main_window.addLabelEntry("Name")
            self.__main_window.addLabelEntry("Surname")
            self.__main_window.addLabelEntry("Username")
            self.__main_window.setStopFunction(self.__main_window.destroyAllSubWindows)
            self.__main_window.addButton("Submit", self.submit)
            self.__main_window.stopSubWindow()
        except ItemLookupError:
            pass

        self.__main_window.setEntry(name="Name", text="", callFunction=False)
        self.__main_window.setEntry(name="Surname", text="", callFunction=False)
        self.__main_window.setEntry(name="Username", text="", callFunction=False)
        self.__main_window.showSubWindow("New profile")

    def submit(self) -> None:
        """
        Implements the new user button action, requesting a new Azure ID and adding the user to the local JSON database.
        :return: None
        """

        name = self.__main_window.getEntry("Name")
        surname = self.__main_window.getEntry("Surname")
        username = self.__main_window.getEntry("Username")
        if self.has_numbers(name) or self.has_numbers(surname):
            self.__main_window.errorBox("TypingErrorBox", "Error: A name can't contain a number", "New profile")

        for users in self.__backend.get_all_users():
            for user in users:
                if user.username == username:
                    self.__main_window.errorBox("UserAlreadyExisting:", "Username already in use, please choose a different "
                                                                       "one", "New profile")
        try:
            self.__backend.new_profile(username, name, surname)
            user = self.__backend.get_by_username(username)
            self.__main_window.addTableRow("UsersTable", [user.username, user.status])
            user_number = self.__backend.get_users_number()
            if user_number == 0 or user_number == 1:
                self.__main_window.setTabbedFrameEnabledTab("MainWindow", "Login", False)
            else:
                self.__main_window.setTabbedFrameEnabledTab("MainWindow", "Login", True)
            self.__main_window.hideSubWindow("New profile")

        except Exception as e:
            self.__main_window.errorBox("Error:", str(e), "New profile")

    @staticmethod
    def has_numbers(s: str) -> bool:
        """
        Sanity check for names and surnames.
        :param s: String to check
        :return: True if the string is deemed valid, False otherwise
        """

        return any(i.isdigit() for i in s)

    def show_db(self) -> None:
        """
        Implements the Users tab in the main window, loading users from the local JSON database, if any.
        :return: None
        """

        self.__main_window.addTable("UsersTable", [["Username", "Status"]]
                                    , action=self.user_action, actionButton=["enrollment", "delete"],
                                    addRow=self.show_new_profile_form)
        all_users = self.__backend.get_all_users()
        for users in all_users:
            for user in users:
                user_row = [user.username, user.status]
                self.__main_window.addTableRow("UsersTable", user_row)

    def user_action(self, btn, row_number) -> None:
        """
        Implements actions for the buttons on each row of the users table, for enrollment and deletion operations.
        :param btn: Button pressed
        :param row_number: Number of the row in which the clicked button is in
        :return: None
        """

        self._row_number = row_number
        if btn == "enrollment":
            status = self.__main_window.getTableRow("UsersTable", self._row_number)[1]
            # fetch azure_id
            if status == "Enrolling":
                self.add_rec_popup()
                # record phase
                self.__main_window.showSubWindow("REC")
            elif status == "Enrolled":
                self.__main_window.infoBox("Attention", "This user is already enrolled in the system.")
            elif status == "Training":
                self.__main_window.infoBox("Attention", "System is in training phase, retry later.")
        if btn == "delete":
            if self.__main_window.yesNoBox("Delete", "Are you sure to delete the selected user?"):
                user = self.__main_window.getTableRow("UsersTable", self._row_number)[0]
                try:
                    self.__backend.delete_profile(username=user)
                    self.__main_window.deleteTableRow("UsersTable", self._row_number)
                except Exception as e:
                    self.__main_window.errorBox("Error", str(e), "New profile")

    # --- --- ---

    # --- Enrollment phase ---
    def add_rec_popup(self) -> None:
        """
        Implements the enrollment pop-up window, showing the enrollment text.
        :return: None
        """

        self.__main_window.startSubWindow("REC")
        text = open(self.__backend.data_directory+"/{text}".format(text=self.__backend.enrollment_fn), "r")
        self.__main_window.addMessage("Play", text="Please read the following text:\n\n {words}".format(words=text.read()))
        text.close()
        self.__main_window.addNamedButton("rec", "enrollment_rec", self.rec_enrollment)
        self.__main_window.setStopFunction(self.__main_window.destroyAllSubWindows)
        self.__main_window.stopSubWindow()

    def rec_enrollment(self) -> None:
        """
        Implements actions for the enrollment buttons, for audio recording and starting the enrollment phase on Azure.
        :return: None
        """

        if self.__main_window.getButton("enrollment_rec") == "rec":
            audio_path = "{base}/audio{ts}.wav".format(base=self.__backend.tmp_directory,
                                                       ts=time.mktime(datetime.utcnow().timetuple()))
            if self.__debug:
                print(audio_path)
            self.__audio = self.__backend.start_recording(audio_path, blocking=False, duration=70)
            self.__main_window.setButton("enrollment_rec", "stop")
        elif self.__main_window.getButton("enrollment_rec") == "stop":
            self.__audio.stop()
            user = self.__main_window.getTableRow("UsersTable", self._row_number)[0]
            usr = self.__backend.get_by_username(username=user)
            self.__main_window.destroyAllSubWindows()
            # actual enrollment
            try:
                op_id = self.__backend.enrollment(azure_id=usr.azure_id, audio_path=self.__audio.path)
                self.__audio.delete()
                time.sleep(self.__backend.operation_check_time)
                result = self.__backend.operation_status(operation_id=op_id,
                                                         enrollment=True,
                                                         identification=False)
                self.__main_window.infoBox("Result", result[1])
                if result[0] not in ("running", "not started", "failed"):
                    self.__backend.update_status(azure_id=usr.azure_id, new_status=result[0])
                    self.__main_window.replaceTableRow("UsersTable", self._row_number, [usr.username, result[0]])
            except Exception as e:
                self.__main_window.errorBox("Error:", str(e))
    # --- --- ---

    def start(self) -> None:
        """
        Starts the GUI.
        :return: None
        """

        self.__main_window.go()


if __name__ == "__main__":
    g = HillMynaGUI()
    g.start()
