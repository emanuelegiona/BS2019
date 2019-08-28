# BS2019
Project for Biometric Systems course (A.Y. 2018/2019), code name: Hill Myna.

## Project structure
```
- Makefile                  # 'make' will take care of all the dependencies required
- hill_myna.py              # Starts the GUI
- backend                   # directory for all the backend source code
    |__ audio.py
    |__ azure.py
    |__ hill_myna_be.py
    |__ rest_client.py
    |__ words.py
- data                      # data needed by Hill Myna to run
    |__ credentials.csv     # Microsoft Azure credentials to access Speech Services and Cognitive Services
- tmp                       # directory for temporary files
- LICENSE                   # GNU AGPL v3.0
- README                    # this file
```

## Funny fact
[Hill myna][1] is one of the many species of birds capable to imitate human speech.
In this project, you will get to repeat random words like a typical hill myna would, in order to get identified and possibly
avoid spoofing techniques such as replay attacks.

[1]: https://en.wikipedia.org/wiki/Common_hill_myna
