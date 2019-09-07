"""
This file contains all the source code needed to handle and query user profiles involved with the identification task.
"""

from collections import namedtuple
from typing import List
import os.path
import json

User = namedtuple("User", "azure_id username name surname status")


class UsersManager:

    """
    This class implements the user manager, handling by using a json file where the user's info will be stored and possibly linked to their AzureID
    """
    def __init__(self, users_path: str):
        """
        UsersManager constructor.
        :param users_path: Path to the users file
        """

        self.__path = users_path

        # Creation of a dictionary for future use, each entry formed by a string and a User
        self.__dictionary = {}

        # creates an empty json if there is no json
        if not os.path.exists(users_path):
            self.__write_file()
        if not os.path.isfile(users_path):
            raise FileNotFoundError("{file} must be a regular file.".format(file=users_path))

        # read from json file and fill the dictionary
        with open(users_path, "r") as read_file:
            users = json.load(read_file)

        print(type(users))
        for azure_id, user in users.items():
            print(azure_id)
            print(user)
            person = User(azure_id=user[0],
                          username=user[1],
                          name=user[2],
                          surname=user[3],
                          status=user[4])

            self.__dictionary[azure_id] = person

    def __write_file(self):
        with open(self.__path, "w") as f:
            json.dump(self.__dictionary, f, indent=4)

    def remove(self, identifier: str) -> None:
        """
        Removes a user from the dictionary
        :param identifier: String containing the azure_id to remove
        :return: None
        """
        if identifier in self.__dictionary:
            self.__dictionary.pop(identifier)

            # update JSON file
            self.__write_file()
        else:
            raise KeyError("The user that should be eliminated does not exist")

    def add(self, azure_id: str, username: str, name: str, surname: str, status: str) -> None:
        """
        Adds a user into a dictionary:
        :param azure_id: Azure id of the new user
        :param username: new user's username
        :param name: name of the user
        :param surname: new user's surname
        :param status: status of the user
        :return: none
        """
        if azure_id in self.__dictionary:
            raise KeyError("Azure_id already existing, insert a new one in order to register the new user")
        for _, values in self.__dictionary.items():
            if username == values.username:
                raise KeyError("Username already taken, please choose one that has not been chosen")

        person = User(azure_id, username, name, surname, status)
        self.__dictionary[azure_id] = person

        # update JSON file
        self.__write_file()

    def update_status(self, azure_id: str) -> None:
        # TODO during the usage, HillMyna should be able to update users' status (AT LEAST)
        pass

    def get_by_azure_id(self, azure_id: str) -> User:
        """
        Returns every information about a user stored in the database
        :param azure_id: contains the Id of a user in order to search for its information
        :return: Returns a dictionary containing every information of a certain user
        """
        if azure_id in self.__dictionary:
            return self.__dictionary[azure_id]
        else:
            raise KeyError("The requested user does not exist in the db. Pls retry with an existent one")

    def get_by_username(self, username: str) -> User:
        """
        Returns every information about a user stored in the database
        :param username: contains the username of a user in order to search for its informations
        :return : Returns a dictionary containing every information of a certain user
        """
        for _, current_user in self.__dictionary.items():
            if username == current_user.username:
                return current_user
        raise KeyError("No user with such username exists. please retry with an existing one")

    def get_all_users(self) -> List[List[User]]:
        """
        The function returns a list of lists, containing each one at most 10 Users.
        :return: A list of lists, each one containing at most 10 Users
        """
        all_users = []
        batch = []
        for _, current_user in self.__dictionary.items():
            batch.append(current_user)

            if len(batch) == 10:
                all_users.append(batch)
                batch = []
        if len(batch) > 0:
            all_users.append(batch)

        return all_users


if __name__ == "__main__":
    um = UsersManager(users_path="../data/users.json")
    um.remove("aaaa")

    l = um.get_all_users()
    print(l)
