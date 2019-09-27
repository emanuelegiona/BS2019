# BS2019
Hill Myna, a voice-only authentication system which aims to take into account spoofing attempts, such as replay attacks.

The main concept is based on an identification task, but it is augmented with a speech recognition task in order to defend its users from replay attacks. In fact, we rely on Microsoft Azure services both for the identification task, using the [Azure Speaker Recognition service][2], and for the speech-to-text task, using the [Azure Speech services][3].

The reason behind combining an identification task with a speech-to-text service is the following: provided the system is undergoing a replay attack, therefore the impostor has some kind of recording of our voice, without the speech-to-text service it might gain an easy access. Indeed, Hill Myna exploits a vocabulary of 100 words whenever a user tries to perform a login operation, by starting a challenge-response mechanism consisting in asking the user to repeat a random sample of words.

Since the words are randomly sampled from the vocabulary, it is highly unlikely that the impostor holds a voice sample containing those exact words, and therefore preventing the attack from being successful.

## Instructions and requirements
Hill Myna has been developed on Ubuntu 18.04 (LTS) with Python 3.6+. In order to run this project, a Makefile has been set up to contain all the required libraries and Python packages; for this reason the suggested routine for running the project is the following:

1. Extract the 'hill_mina.zip' contents to a directory named 'hill_myna', in case of ZIP download; otherwise, clone this repository.
2. Move into the 'hill_myna' directory, containing 'Makefile', 'hill_myna.py' files, 'data', 'tmp' directories.
3. Run 'make' in this directory for installing all the required dependencies.
4. Run 'python hill_myna.py' and the GUI will be shown.
5. Follow instructions in the GUI.


## Project structure
```
- Makefile                  # 'make' will take care of all the dependencies required
- hill_myna.py              # Starts the GUI
- backend                   # directory for all the backend source code
    |__ audio.py
    |__ azure.py
    |__ hill_myna_be.py
    |__ rest_client.py
    |__ users.py
    |__ words.py
- data                      # data needed by Hill Myna to run
    |__ credentials.csv     # Microsoft Azure credentials to access Speech Services and Cognitive Services
    |__ enrollment.txt      # Text users have to read for enrollment reasons
    |__ words.txt           # Words for anti-spoofing reasons
- tmp                       # directory for temporary files
- LICENSE                   # GNU AGPL v3.0
- README                    # this file
```

## Funny fact
[Hill myna][1] is one of the many species of birds capable of imitating human speech.
In this project, you will get to repeat random words like a typical hill myna would, in order to get identified and possibly
avoid spoofing techniques such as replay attacks.

[1]: https://en.wikipedia.org/wiki/Common_hill_myna
[2]: https://westus.dev.cognitive.microsoft.com/docs/services/563309b6778daf02acc0a508
[3]: https://docs.microsoft.com/it-it/azure/cognitive-services/speech-service/rest-speech-to-text