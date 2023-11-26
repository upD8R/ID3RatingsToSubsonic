# Copy ID3 ratings from MP3 to Subsonic

This script can recursively scan your MP3 files, it extracts the rating from the ID3 tags and eventually writes the result into a Subsonic server by using the "old" API (not OpenSubsonic). It is motivated and influenced by [Transfer Plex Ratings to Subsonic](https://github.com/profesaurus/transfer_plex_ratings_to_subsonic) and is tailored to and tested only with my own setup: MP3 files accessible on a SMB share and the Subsonic server used is [Navidrome](https://www.navidrome.org/). 

## Background/Motivation

I use Navidrome (Docker based on Raspberry Pi 4) to serve my music library locally and on the go (with Wireguard VPN) by using [Symfonium](https://symfonium.app/) as Subsonic client. Considering all the different music streaming services available today this sounds old school but it works for me. Anyway, in the past I used plain MP3 players or Emby to create smart playlists based on MP3 ratings, e.g. play all songs with ratings better than 3. In order to achieve this I made sure the ratings are properly stored in the ID3 tag.

There are different fields in ID3, which refer to ratings, usually dependent on the tools originally used to populate them, e.g. **Rating MM** is used by [MediaMonkey](https://www.mediamonkey.com), **Rating WMP** by Windows Media Player etc. You can watch and change such tags with tools like [mp3tag](https://www.mp3tag.de). 
Luckily, there is one "generic" tag called popularimeter or short **POPM**, which can be used. It consists of more than just the rating, e.g. an email address but I ignore this and just use the rating value.

## Prerequisites

### Python and its dependencies

My script requires Python 3, so make sure it is installed on your system by e.g. executing 

	python3 --version
	Python 3.7.3

In case Python 3 is not your default Python version and/or you don't have the corresponding pip version installed yet, the following might help:

	sudo apt install python3-pip

The script uses two Python libraries: [py-sonic](https://github.com/crustymonkey/py-sonic) to enable the communication with the Subsonic API and [eyeD3](https://eyed3.readthedocs.io/) to ease the access to the ID3 tags. You can install them with pip/pip3. 

	pip3 install py-sonic eyed3

### MP3 storage location

Your MP3 files need to be accessible on system level to the script, so either they are stored locally or mounted correspondingly. It should be obvious but the MP3s we are talking about shoul be the same library, which you linked to your Subsonic server.

## Usage

The Subsonic server credentials and details need to be given within the script, so please change those values according to your needs:

	# Subsonic settings
	subsonic_url = 'http://subsonic.server'
	subsonic_username = 'username'
	subsonic_password = 'password'
	subsonic_port = port number

After installing the necessary libraries you can just launch the script by executing

	python3 copyRatings_from_MP3_to_Navidrome.py </path/to/your/MP3s/>

If you add -s as parameter the actual update of the ratings in the Subsonic server is skipped - so this is rather safe to test whether access to your MP3s works and whether the script can fund the corresponding matches in the Subsonic server.

	python3 copyRatings_from_MP3_to_Navidrome.py -s </path/to/your/MP3s/>

In any case there are no write actions on the MP3 files, only the Subsonic database will be updated with a rating, if found.

## Disclaimer

**Use this script at your own risk.**
I developed it for my very personal use case, so it may or may not work in your environment.

Depending on the size of your library the update will take several minutes but the script tries to give an indication where it is in the process, most time is usually spent by reading the ID3 tags.
