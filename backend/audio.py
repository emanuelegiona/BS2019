"""
This file contains source code for all the audio processing involved in this project.
"""
import sounddevice as sd
import soundfile as sf
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
        self.path = path
        self.audio = None
        self.block = blocking

    def rec(self, duration: float, fs: int = sd.default.samplerate):
        """
        Records and returns an audio sample from default device. If path is not None, the sample will be locally stored
        to path.
        :param duration: is an integer that indicates how many seconds of recording will be performed.
        :param fs: is the frequency sampling (sampling rate) of the captured audio expressed as an integer
        otherwise.
        :return: the recorded audio.
        """
        print("Start Recording")
        # recorded audio as a NumPy array
        self.audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, blocking=self.block)
        if self.path is not None and self.block is True:
            print("End Recording")
            sf.write(self.path, self.audio, fs)
        return self.audio

    def read_from_file(self, path: str):
        """
        Read an audio file already stored in the FS.
        :param path: is a string representing the path where the audio is stored in.
        :return: the audio data and the related sample rate.
        """
        data, fs = sf.read(path, dtype='float32')
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
            sf.write(self.path, self.audio, self.get_sample_rate())

    def wait(self):
        """
        If the recording was already finished, this returns immediately; if not, it waits and returns as soon as the
        recording is finished.
        :return: a flag indicating the status of recording.
        """
        return sd.wait()


if __name__ == "__main__":
    a = Audio(path="ok.wav")
    b = a.rec(duration=6.0)
    sd.play(b, 16000)
