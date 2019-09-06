"""
This file contains all the source code needed to handle and query user profiles involved with the identification task.
"""

from collections import namedtuple
from datetime import datetime
from typing import List
import time
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

        # Creation of a dictionary for future use, feach entry formed by a string and a User
        # self.UsId: {} : add if in need of a second dictionary

        self.AzId = {}

        # creates an empty json if there is no json
        if not os.path.exists(users_path):
            with open(users_path, 'w') as datb:
                json.dump([], datb)
        if not os.path.isfile(users_path):
            raise FileNotFoundError("{file} must be a regular file.".format(file=users_path))


        # read from json file and AzId fill

        with open(users_path, "r") as read_file:
            users= json.load(read_file)
            for user in users:
                person = User(user, user["username"], user["name"], user["surname"], user["status"])
                self.AzId[user] = person

    def remove (self, identifier : str) -> None:

        """
        Removes a user from the dictionary
        :param identifier: String containing the azure_id to remove
        :return: None
        """
        if identifier in self.AzId:
            self.AzId.pop(identifier)
        else : raise KeyError("The user that should be eliminated does not exist")

    def add(self, azure_id : str, username: str, name : str, surname : str, status : bool) -> None:
        """
        Adds a user into a dictionary:
        :param azure_id: Azure id of the new user
        :param username: new user's username
        :param name: name of the user
        :param surname: new user's surname
        :param status: status of the user
        :return: none
        """
        if azure_id in self.AzId:
            raise KeyError("Azure_id already existing, insert a new one in order to register the new user")
        for x in self.AzId:
            if username in self.AzId["username"]:
                raise KeyError("Username already taken, please choose one that has not been chosen")

        person = User(azure_id, username, name, surname, status)
        self.AzId[azure_id] = person

    def get_Azure_Id(self, azure_id) -> User:
        """
        Returns every information about a user stored in the database
        :param azureId: contains the Id of a user in order to search for its informations
        :return: Returns a dictionary containing every information of a certain user
        """
        if azure_id in self.AzId:
            return User(self.AzId.get(azure_id).azure_id, self.AzId.get(azure_id).username, self.AzId.get(azure_id).name
                        , self.AzId.get(azure_id).surname,self.AzId.get(azure_id).status)
        else : raise KeyError("The requested user does not exist in the db. Pls retry with an existent one")

    def get_Username(self, username) -> User:
        """
        Returns every information about a user stored in the database
        :param username: contains the username of a user in order to search for its informations
        :return : Returns a dictionary containing every information of a certain user
        """
        for id, value in self.AzId.values() :
            if username == self.AzId.get(id).username:
                return self.get_Azure_Id(self.AzId.get(id).azure_id)
        raise KeyError("No user with such username exists. please retry with an existing one")

    def ten_Users_List (self) -> List:
        """
        The function returns a list of lists, containing each one at most 1o Users.
        :return: A list of lists, each one containing at most 10 Users
        """
        x, y = 0
        bunch = []
        aux = []
        # for cycles AzId and takes every user, dividing them in groups of 10 users at most
        for user in self.AzId:
            if y >= 10:
                bunch.append(aux.copy())
                y = 0
            person = self.AzId.get(user)
            aux.append(person.copy())
            x = x + 1
        return list










"""if __name__ == "__main__":

        prova = UsersManager(users_path="../data/datb.json")
        prova=({'emanuele': {'angelo': 'matteo'}})
        print(prova)
        prova.remove("emanuele")
        print(prova)
"""







