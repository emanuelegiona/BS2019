"""
This file contains source code for all the audio processing involved in this project.
"""
import sounddevice as sd
import soundfile as sf

"""
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

# Records and returns an audio sample from default device. If path is not None, the sample will be locally stored to path.
# @duration is an integer that indicates how many seconds of recording will be performed.
# @fs is the frequency sampling (sampling rate) of the captured audio expressed as an integer.
# @path is string representing the path where the audio will be stored in.
# @block is a boolean. If it's true won't be possible to launch other commands during the recording exection, yes otherwise.
def rec(duration, fs=16000, path=None, block=False):
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, blocking=block) #recorded audio as a NumPy array
    if path is not None:
        sf.write(path, myrecording, fs)
    return myrecording



