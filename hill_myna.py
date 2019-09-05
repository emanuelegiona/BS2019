"""
This file contains source code for starting the GUI of Hill Myna.
"""

from hill_myna_be import HillMyna
from appJar import gui


class HillMynaGUI:
    """
    Class implementing HillMyna GUI.
    """

    def __init__(self):
        self.__backend = HillMyna(data_directory="data",
                                  tmp_directory="tmp")

        self.__main_window = gui()
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
        self.__main_window.addLabel("Test")
        self.__main_window.stopTab()
        # --- --- ---

        self.__main_window.stopTabbedFrame()

    def login_function(self):
        print("Loggin in...")
        self.__main_window.removeAllWidgets()
        self.add_tabs(main_window=False)

    def start(self):
        self.__main_window.go()


if __name__ == "__main__":
    print("Hill Myna 0.0\nA biometric system project where you get to repeat words")
    g = HillMynaGUI()
    g.start()
