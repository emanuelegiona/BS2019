"""
This file contains source code for starting the GUI of Hill Myna.
"""

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
        self.__users_manager = self.__backend.get_users_manager()
        self.add_tabs()
        self.__main_window.setTitle("Hill Myna")
        self.__main_window.setSize(700, 500)
        self.__main_window.setResizable(False)

    def add_tabs(self, main_window: bool = True):
        self.__main_window.startTabbedFrame("MainWindow")

        # --- main login form ---
        self.__main_window.startTab("Login")
        self.__main_window.addLabel("Welcome to Hill Myna!")

        if main_window:
            self.__main_window.addLabel("Click on the button to start recording to get identified.")
            self.__main_window.addButton("Login", func=self.login_function)
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
        self.__main_window.removeAllWidgets()
        self.add_tabs(main_window=False)

    def start(self):
        self.__main_window.go()

    def show_new_profile_form(self):
        self.__main_window.openTab("MainWindow","Users")
        self.__main_window.addLabel("userLab", "Username:", 0, 0)
        self.__main_window.addEntry("userEnt", 0, 1)
        self.__main_window.addLabel("nameLab", "Name:", 1, 0)
        self.__main_window.addEntry("nameEnt", 1, 1)
        self.__main_window.addLabel("surLab", "Surname:", 2, 0)
        self.__main_window.addEntry("surEnt", 2, 1)
        self.__main_window.addButtons(["Submit", "Cancel"], None, colspan=2)
        self.__main_window.closeTab("Users")

    def show_db(self):
        self.__main_window.addTable("g1",  [["Username", "Status"]]
                                    , action=self.fire, actionButton=["edit", "new enrollment", "delete"],
                                    addRow=self.login_function)
        um = self.__users_manager
        users = um.get_all_users()
        for user in users[0]:
            user = [user[1], user[4]]
            self.__main_window.addTableRow("g1", user)

    def fire(self, btn, row_number):
        print(self.__main_window.getTableRow("g1", row_number))
        print(btn)
        print(self.__backend.get_words())
        if btn == "new enrollment":
            user = self.__main_window.getTableRow("g1", row_number)[0]
            status = self.__main_window.getTableRow("g1", row_number)[1]
            # fetch azure_id
            if status == "Enrolling":
                azure_id = None
                usr = self.__users_manager.get_by_username(username=user)
                # enrollment
                # TODO while usr.status == self.ENROLLING --> maybe in the GUI
                # record
                audio_path = "{base}/audio{ts}.wav".format(base=self.__backend.tmp_directory,
                                                           ts=time.mktime(datetime.utcnow().timetuple()))
                audio = Audio(path=audio_path,
                              blocking=True)
                self.__backend.get_words()
                audio.rec(duration=6)
                # actual enrollment
                op_id = self.__backend.enrollment(azure_id=usr.azure_id, audio_path=audio_path)
                result = self.__backend.operation_status(operation_id=op_id,
                                               enrollment=True,
                                               identification=False)
                print(result)
                audio.delete()
                #print(self.__backend.get_speaker_client().get_profile(profile_id=usr.azure_id))
                print(usr)


if __name__ == "__main__":
    print("Hill Myna 0.0\nA biometric system project where you get to repeat words")
    g = HillMynaGUI()
    g.start()
