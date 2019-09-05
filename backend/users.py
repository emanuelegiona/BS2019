"""
This file contains all the source code needed to handle and query user profiles involved with the identification task.
"""

from collections import namedtuple
from datetime import datetime
from typing import List
import time
import os.path
import json

# TODO avrei unito Info e User in un unico concetto (come namedtuple)
Info = namedtuple("AzureId", "User")        # TODO Info = namedtuple("Info", "AzureId User") ti crea un simil-oggetto con campi "AzureId" ed "User"


class User:

    def __init__(self, azure_id: str, username: str, name: str, surname: str, status: bool):
        person = {"azure_id": azure_id,
                  "username": username,
                  "name": name,
                  "surname": surname,
                  "status": status}


def getUser(self, id: str) -> dict:
    if id == self.person["azure_id"]:
        return self.person
    else:
        raise KeyError("The user searched is not this one. please retry")

class UsersManager:

    """
    This class implements the user manager, handling by using a json file where the user's info will be stored and possibly linked to their AzureID
    """
    def __init__(self, users_path: str):
        """
        UsersManager constructor.
        :param users_path: Path to the users file
        """

        # Creation of a dictionary for future use

        # self.UsId: {} : add if in need of a second dictionary

        self.AzId = {}                      # TODO lo renderei un dict con chiavi str e valori Info/User (dopo l'unione dei concetti in namedtuple)
        if not os.path.exists(users_path):
            raise FileNotFoundError("{file} not found.".format(file=users_path))
        if not os.path.isfile(users_path):
            raise FileNotFoundError("{file} must be a regular file.".format(file=users_path))


        #read from json file and AzId fill
        with open(users_path, "r") as read_file:
            users= json.load(read_file)
            for user in users:
                self.AzId.add(user)         # TODO dict non ha metodo add, lo aggiungi semplicemente AzId["nuova chiave"] = "nuovo valore"

                #add(user, UsId)

    def remove (self, id : str) -> None:

        """
        Removes a user from the dictionary
        :param id: String containing the azure_id to remove
        :return: None
        """
        if id in self.AzId:
            self.AzId.pop(id)
        else : raise KeyError("The user that should be eliminated does not exist")

    def add(self, person) -> None:
        """
        Adds a user into a dictionary:
        :param person: User object to add in the database
        :return: none
        """
        values = person.copy()
        values.pop("AzureId")
        key = person.x("AzureId")
        self.AzId.update(key, values)           # TODO v. riga 58

    def getAz(self, azureId) -> Info:
        """
        Returns every information about a user stored in the database
        :param azureId: contains the Id of a user in order to search for its informations
        :return: Returns a dictionary containing every information of a certain user
        """
        if azureId in self.AzId:
            info = {}
            info.update("azureId", azureId)     # TODO v. riga 58
            aux = (self.AzId.get(azureId)).copy
            for x in aux :
                info.update(x , aux.get(x))     # TODO v. riga 58
            return info                         # TODO type mismatch: returned dict invece di Info
        else : raise KeyError("The requested user does not exist in the db. Pls retry with an existent one")

    def getId(self, username) -> Info:
        """
        Returns every information about a user stored in the database
        :param username: contains the username of a user in order to search for its informations
        :return : Returns a dictionary containing every information of a certain user
        """
        for id in self.AzId :       # TODO iterazione più semplice con "for id, value in self.AzId.values()" - visto che spacchetta le chiavi e valori unitamente dal dizionario
            if username == (self.AzId.get(id)).get("Name"):
                aux = self.AzId.get(id)
                y = aux["azure_id"]
                x = User(id, aux["username"], aux["name"], aux["surname"], aux["status"] )
                info = Info(y , x)  # TODO Info ha solo 1 campo (v. riga 13)
                return info
        raise KeyError("No user with such username exists. please retry with an existing one")






"""if __name__ == "__main__":

        prova = UsersManager(users_path="../data/datb.json")
        prova=({'emanuele': {'angelo': 'matteo'}})
        print(prova)
        prova.remove("emanuele")
        print(prova)
"""







