"""
This file contains source code for starting the GUI of Hill Myna.
"""
from appJar.appjar import ItemLookupError
from hill_myna_be import HillMyna
from appJar import gui
import time
from audio import Audio
from datetime import datetime


class HillMynaGUI:
    """
    Class implementing HillMyna GUI.
    """

    def __init__(self):
        self.__backend = HillMyna(data_directory="data",
                                  tmp_directory="tmp")

        self.__main_window = gui()
        self._row_number=None
        self.add_tabs()
        self.__main_window.setTitle("Hill Myna")
        self.__main_window.setSize(700, 500)
        self.__main_window.setResizable(True)

    def add_tabs(self, main_window: bool = True):
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
        if self.__backend.get_users_number() is 0:
            self.__main_window.setTabbedFrameSelectedTab("MainWindow", "Users")
            self.__main_window.setTabbedFrameDisabledTab("MainWindow", "Login")
        # --- --- ---
        self.__main_window.stopTabbedFrame()

    def login_function(self):
        print("Loggin in...")
        self.__main_window.openTab("MainWindow", "Login")
        self.__main_window.emptyCurrentContainer()
        self.__display_words = self.__backend.get_words()
        words = ""
        for word in self.__display_words:
            words += "- "+word+"\n"
        self.__main_window.message("Repeat", "Whenever you're ready, click rec and repeat the following terms:\n\n" + words)
        self.__main_window.addNamedButton("rec", "identification_rec", self.rec_identification)
        self.__main_window.stopTab()

    def logout_function(self):
        self.__main_window.openTab("MainWindow", "Login")
        self.__main_window.emptyCurrentContainer()
        self.__main_window.addLabel("Click on the button to start login procedure.")
        self.__main_window.addButton("login", func=self.login_function)
        self.__main_window.stopTab()

    def rec_identification(self, btn):
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
                print("Recognizing words...")
                recognized_words = set(self.__backend.speech_to_text(self.__audio.path))
                print("Expected: {w}".format(w=self.__display_words))
                print("Recognized: {w}".format(w=recognized_words))
                print("Correctly recognized {n} words".format(n=len(recognized_words.intersection(set(self.__display_words)))))
                if len(recognized_words.intersection(set(self.__display_words))) > 0:
                    self.__main_window.setMessage(title="identification_status", text="Identifying user...")
                    print("Identifying user...")
                    user = self.__backend.identification(self.__audio.path, short_audio=True)
                    self.__main_window.setMessage(title="identification_status", text="Logged in as {user}".format(user=str(user.username)))
                    self.__main_window.addButton("logout", func=self.logout_function)
                    self.__audio.delete()
            except Exception as e:
                self.__audio.delete()
                self.__main_window.errorBox("Error:", str(e))

    def start(self):
        self.__main_window.go()

    def show_new_profile_form(self):
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

    def submit(self):
        name = self.__main_window.getEntry("Name")
        surname = self.__main_window.getEntry("Surname")
        username = self.__main_window.getEntry("Username")
        if self.has_numbers(name) or self.has_numbers(surname):
            self.__main_window.errorBox("TypingErrorBox", "Error: A name can't contain a number", "New profile")
        for user in self.__backend.get_all_users()[0]:
            if user.username == username:
                self.__main_window.errorBox("UserAlreadyExisting:", "Username already in use, please choose a different "
                                                                   "one", "New profile")
        try:
            self.__backend.new_profile(username, name, surname)
            user = self.__backend.get_by_username(username)
            self.__main_window.addTableRow("UsersTable", [user.username, user.status])
            if self.__backend.get_users_number() == 1:
                self.__main_window.setTabbedFrameEnabledTab("MainWindow", "Login", False)
            self.__main_window.hideSubWindow("New profile")

        except Exception as e:
            self.__main_window.errorBox("Error:", str(e), "New profile")

    @staticmethod
    def has_numbers(s: str) -> bool:
        return any(i.isdigit() for i in s)

    def show_db(self):
        self.__main_window.addTable("UsersTable", [["Username", "Status"]]
                                    , action=self.user_action, actionButton=["enrollment", "delete"],
                                    addRow=self.show_new_profile_form)
        all_users = self.__backend.get_all_users()
        for users in all_users:
            for user in users:
                user_row = [user.username, user.status]
                self.__main_window.addTableRow("UsersTable", user_row)

    def user_action(self, btn, row_number):
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

    def add_rec_popup(self):
        self.__main_window.startSubWindow("REC")
        text = open(self.__backend.data_directory+"/{text}".format(text=self.__backend.enrollment_fn), "r")
        self.__main_window.addMessage("Play", text="Please read the following text:\n\n {words}".format(words=text.read()))
        text.close()
        self.__main_window.addNamedButton("rec", "enrollment_rec", self.rec_enrollment)
        self.__main_window.setStopFunction(self.__main_window.destroyAllSubWindows)
        self.__main_window.stopSubWindow()

    def rec_enrollment(self):
        if self.__main_window.getButton("enrollment_rec") == "rec":
            audio_path = "{base}/audio{ts}.wav".format(base=self.__backend.tmp_directory,
                                                       ts=time.mktime(datetime.utcnow().timetuple()))
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
                    self.__backend.update_status(usr.azure_id, result[0])
            except Exception as e:
                self.__main_window.errorBox("Error:", str(e))


if __name__ == "__main__":
    print("Hill Myna 0.0\nA biometric system project where you get to repeat words")
    g = HillMynaGUI()
    g.start()
