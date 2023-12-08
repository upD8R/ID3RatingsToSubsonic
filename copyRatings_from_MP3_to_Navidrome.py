#!/usr/bin/env python3

####################################################################
##
## Script to extract MP3 ratings and write them to a Subsonic server
##
####################################################################

import argparse
import os
import eyed3
import sys
import libsonic

eyed3.log.setLevel("ERROR")

# Subsonic settings
subsonic_url = 'http://subsonic.server'
subsonic_username = 'username'
subsonic_password = 'password'
subsonic_port = 4533

musicDict = {}
subsonic = libsonic.Connection(subsonic_url, subsonic_username, subsonic_password, port=subsonic_port, appName='MP3/Subsonic rating script')

def populate_dictionary():
    print("\n>> Getting all indexes from Subsonic server...")
    indexes = subsonic.getIndexes()
    for index in indexes['indexes']['index']:
        print(">>>> Reading songs from artists starting with " + index['name'] + "...  \r", end='')
        for artist in index['artist']:
            albums = subsonic.getArtist(artist['id'])
            for album in albums['artist']['album']:
                songs = subsonic.getAlbum(album['id'])
                for song in songs['album']['song']:
                    path_parts = song['path'].split('/') # nur Dateiname 1/2
                    last_two_parts = '/'.join(path_parts[-2:])
                    musicDict[last_two_parts] = song['id'] # nur Dateiname

def map_to_five_star_rating(value):
    if value == 0:
        return 0  # Keine Bewertung
    # Linear Mapping: 1-255 auf 1-5
    return round(1 + (value - 1) * 4 / 254)

def get_mp3_files(directory):
    mp3_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp3"):
                mp3_files.append(os.path.join(root, file))
                print(f">> Counting MP3 files: {len(mp3_files)}  \r", end='')
    return mp3_files

def get_rating_from_id3(file_path):
    audiofile = eyed3.load(file_path)
    if audiofile.tag:
        for frame in audiofile.tag.frameiter(["POPM"]):
            return frame.rating
    return None

# ersetzt / durch _ im Titel
def get_title_from_id3(file_path):
    audiofile = eyed3.load(file_path)
    if audiofile.tag:
        for frame in audiofile.tag.frameiter(["TIT2"]):
            original_title = frame.text
            # Ersetze "/" durch "_"
            cleaned_title = original_title.replace("/", "_")
            return cleaned_title
    return None

def get_track_number_from_id3(file_path):
    audiofile = eyed3.load(file_path)
    if audiofile.tag:
        for frame in audiofile.tag.frameiter(["TRCK"]):
            track_number = frame.text
            # Extrahiere nur die Tracknummer vor dem '/' (falls vorhanden)
            track_number = track_number.split('/')[0].strip()
            # Füge eine führende Null hinzu, wenn die Tracknummer einstellig ist
            return track_number.zfill(2)
    return None

def get_album_title_from_id3(file_path):
    audiofile = eyed3.load(file_path)
    if audiofile.tag:
        for frame in audiofile.tag.frameiter(["TALB"]):
            return frame.text
    return None

def populate_dictionary_with_ratings():
    print("\nThis script deletes existing user ratings in a Subsonic server, use it on your own risk!\nSimulation mode (-s) is ignored, changes will be executed on Subsonic server!")

    go_on = input("\nDo you want to proceed? (yes/NO) ")
    if go_on.lower() != 'yes':
        return
    else:
        print('')

    print(">> Getting all songs from Subsonic server...")
    indexes = subsonic.getIndexes()
    progress = 0
    print("Deleted user ratings: 0\r", end='')
    for index in indexes['indexes']['index']:
        for artist in index['artist']:
            albums = subsonic.getArtist(artist['id'])
            for album in albums['artist']['album']:
                songs = subsonic.getAlbum(album['id'])
                for song_info in songs['album']['song']:
                    if 'userRating' in song_info and song_info['userRating'] > 0:
                        progress = progress + 1
                        musicDict[song_info['id']] = song_info['userRating']
                        subsonic.setRating(song_info['id'], 0)
                        print(f"Deleted user ratings: {progress}\r", end='')
    print("\n>> Finished deleting user ratings.")

def main(directory, skip_subsonic=False, delete_user_ratings=False):
    print("\nThis script reads ID3 tag ratings of all MP3s in the given directory (recursively) and\nwrites them into the 5-star user rating value of a Subsonic server.\n\nPlease note: Existing ratings of affected songs in Subsonic will be REPLACED!\nDepending on the number of MP3 files, this process may take a while. Please be patient!")

    go_on = input("\nDo you want to proceed? (yes/NO) ")
    if go_on.lower() != 'yes':
        return
    else:
        print('')

    mp3_files = get_mp3_files(directory)

    if not mp3_files:
        print(f"\nCouldn't find any MP3 files in {directory}")
        return

    if delete_user_ratings:
        populate_dictionary_with_ratings()
        return

    populate_dictionary()
    file_counter = 0
    songs_updated = 0
    print('')

    for mp3_file in mp3_files:
        file_counter = file_counter + 1
        str_mp3_files = str(len(mp3_files))
        rating = get_rating_from_id3(mp3_file)
        title = get_title_from_id3(mp3_file)
        track_number = get_track_number_from_id3(mp3_file)
        album_title = get_album_title_from_id3(mp3_file)
        album_und_song = f"{album_title}/{track_number} - {title}.mp3"
        if rating is not None:
            str_file_counter = str(file_counter)
            filler_file_counter = str_file_counter.zfill(len(str_mp3_files))
            print(f"Song: {filler_file_counter}/{len(mp3_files)}\t\tNew Rating: {map_to_five_star_rating(rating)}\t\tMP3: {album_und_song}")

            if not skip_subsonic:
                subsonic.setRating(musicDict[album_und_song], map_to_five_star_rating(rating))
                songs_updated = songs_updated + 1

    print(f"\n>> Updated {songs_updated} rating(s) in Subsonic")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to copy user ratings from MP3 IDs to a Subsonic server or to delete user ratings in Subsonic")
    parser.add_argument("directory", nargs="?", help="The directory containing your MP3s (also subfolders will be considered)")
    parser.add_argument("-s", "--skip-subsonic", action="store_true", help="Skip Subsonic rating update (simulation mode)")
    parser.add_argument("-d", "--delete-user-ratings", action="store_true", help="Delete user ratings from Subsonic server")

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
    else:
        directory = args.directory
        skip_subsonic = args.skip_subsonic
        delete_user_ratings = args.delete_user_ratings

        if delete_user_ratings:
            populate_dictionary_with_ratings()
        else:
            main(directory, skip_subsonic, delete_user_ratings)
