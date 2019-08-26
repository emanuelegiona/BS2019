all: libs pip

libs:
	@echo "\nInstalling required packets using APT\n"
	sudo apt install libportaudio2

pip:
	@echo "\nInstalling Python packages using PIP\n"
	pip install scipy
	pip install sounddevice
