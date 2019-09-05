"""
This file contains source code for all the audio processing involved in this project.
"""
import sounddevice as sd
import soundfile as sf
import os
import time
from pydub import AudioSegment
"""
useful libraries for eventual implementation of silence removal:

import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment,silence
from pydub.playback import play

Example of usage of sounddevice library:
source: https://python-sounddevice.readthedocs.io/en/0.3.13/usage.html
fs=16000 #sampling rate 16 kHz
sd.default.samplerate = fs
duration = 5.0  # seconds
myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
sd.wait()
sd.play(myrecording, fs)
sf.write(path, myrecording, fs)
data, fs = sf.read(path, dtype='float32') #to read an already existing audio sample from FS
sd.play(data, fs)
sd.wait()
"""
sd.default.samplerate = 16000


class Audio:

    def __init__(self, path: str = None, blocking: bool = False):
        """
        :param path: the path where the audio will be stored in.    # TODO full path ?
        :param blocking: a flag that indicates if the recording will be blocking or not.
        """
        self.path = path
        self.start = None
        self.end = None
        self.audio = None
        self.block = blocking

    def rec(self, duration: float, fs: int = sd.default.samplerate):
        """
        Records and returns an audio sample from default device. If path is not None, the sample will be locally stored
        to path.
        :param duration: is an integer that indicates how many seconds of recording will be performed.
        :param fs: is the frequency sampling (sampling rate) of the captured audio expressed as an integer
        otherwise.
        """
        print("Start Recording")
        self.start = time.time()
        # recorded audio as a NumPy array
        self.audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, blocking=self.block)
        if self.path is not None and self.block is True:
            self.end = time.time()
            print("End Recording")
            sf.write("../tmp/{file}".format(file=self.path), self.audio, fs)        # TODO v. riga 37

    def read_from_file(self):
        """
        Read the audio file stored in the FS.
        :return: the audio data (as a Numpy array) and the related sample rate (as an integer).
        """
        data, fs = sf.read("../tmp/{file}".format(file=self.path), dtype='float32')     # TODO v. riga 37
        return data, fs

    def set_sample_rate(self, sm: int):
        """
        Set the sample rate for recording.
        :param sm: is the frequency sampling (sampling rate) of the captured audio expressed as an integer.
        """
        sd.default.samplerate = sm

    def get_sample_rate(self):
        """
        Return the sample rate for recording.
        :return the frequency sampling (sampling rate) of the captured audio expressed as an integer.
        """
        return sd.default.samplerate

    def stop(self):
        """
        Stops a non blocking rec() during an audio acquisition. The registration is immediately terminated without
        waiting for the timeout expressed by the duration argument of rec.
        """
        sd.stop()
        if self.path is not None:
            print("End Recording")
            self.end = time.time()
            sf.write("../tmp/{file}".format(file=self.path), self.audio, self.get_sample_rate())    # TODO v. riga 37
            duration = self.get_real_duration() * 1000
            audio = AudioSegment.from_wav("../tmp/{file}".format(file=self.path))[:duration]        # TODO v. riga 37
            self.delete()
            audio.export("../tmp/{file}".format(file=self.path), format="wav")                      # TODO v. riga 37
            self.audio, fs = self.read_from_file()

    def wait(self):
        """
        If the recording was already finished, this returns immediately; if not, it waits and returns as soon as the
        recording is finished.
        :return: a flag indicating the status of recording.
        """
        return sd.wait()

    def delete(self):
        """
        Delete the recorded audio from FS.
        """
        if self.start is not None:
            os.remove("../tmp/{file}".format(file=self.path))                       # TODO v. riga 37
        else:
            raise FileNotFoundError("{file} not found.".format(file=self.path))     # TODO v. riga 37

    def get_real_duration(self):
        """
        In case of non-blocking audio this method returns the real duration of the audio, removing eventual final
        silences.
        :return: an integer indicating the real audio duration.
        """
        return self.end - self.start


if __name__ == "__main__":
    a = Audio("franco.wav")
    a.rec(60)
    time.sleep(5)
    a.stop()
    data, fs= sf.read("/tmp/franco.wav")
    sd.play(data,fs)
