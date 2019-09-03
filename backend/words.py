"""
This file contains all the source code needed to handle and query the words database for anti-spoofing reasons.
"""
import os
from random import sample
from typing import List


class WordManager:
    """
    This class implements a word manager for anti-spoofing reasons.
    """
    
    def __init__(self, words_path: str, debug: bool = False):
        """
        WordManager constructor.
        :param words_path: Path to the words file, expected to be a TXT file containing a single word on each line
        :param debug: if True, debug messages are printed to the standard output
        """

        if not os.path.exists(words_path):
            raise FileNotFoundError("{file} not found.".format(file=words_path))
        if not os.path.isfile(words_path):
            raise FileNotFoundError("{file} must be a regular file.".format(file=words_path))

        self.words = set()
        self.__debug = debug

        if self.__debug:
            print("Reading words file {file}...".format(file=words_path))

        with open(words_path) as file:
            for line in file:
                line = line.strip("\n")

                if len(line) <= 0:
                    continue

                self.words.add(line)

        if self.__debug:
            print("Done: {num} words in the dictionary.".format(num=len(self.words)))

    def get_words(self, number: int = 5) -> List[str]:
        """
        Returns a list of randomly chosen words of the given size. The returned list contains no duplicates.
        :param number: Number of words to be sampled from the dictionary
        :return: No-duplicate list of randomly chosen words
        """

        assert number > 1, "Number of sampled words cannot be negative or 1"
        ret = sample(population=self.words,
                     k=number)
        if self.__debug:
            print("Sampled words: {list}".format(list=", ".join(ret)))

        return ret


if __name__ == "__main__":
    m = WordManager(words_path="../data/words.txt",
                    debug=True)
    w = m.get_words()
