
import os
import time

from dotenv import load_dotenv

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from printplus import PrintPlus

from dbHelper import DBHelper
from utilities import *

class SpotifyDl:
    def __init__(self,useDb=True,saveLocation='songs',dbName='spotipyDb'):
        """

        """
        self.saveLocation = saveLocation
        if not os.path.isdir(saveLocation):
            os.mkdir(saveLocation)
        
        self.dbHelper = None
        self.useDb = useDb
        if useDb:
            self.dbHelper = DBHelper(dbName)
        
        self.sp=None
        self.printer = PrintPlus()
        self.uid = None
        self.name = None
        
    
    def login(self):
        """
            Login to user account 
        """
        #Loading Credentials from .env file. Remove load_dotenv() and replace arguments with credentials
        #Get Credentials from https://developer.spotify.com/dashboard

        load_dotenv()
        self.sp = spotipy.Spotify(client_credentials_manager=SpotifyOAuth(client_id=os.getenv('SPOTIFY_CLIENT'),
                                               client_secret=os.getenv('SPOTIFY_SECRET'),
                                               redirect_uri="http://localhost:8080",
                                               scope="playlist-read-private,user-library-read,user-read-currently-playing,user-read-playback-state,playlist-modify-private,user-modify-playback-state"))
        
        me = self.sp.me()
        self.uid = me['id']
        self.name = me['display_name']


    def getAllSavedSongs(self):
        offset = 0
        songs = self.sp.current_user_saved_tracks()
        nxt= songs['next']
        all_songs = songs['items']
        while nxt != None:
            offset += 20 
            songs = self.sp.current_user_saved_tracks(offset=offset)
            nxt= songs['next']
            all_songs.extend(songs['items'])
        return all_songs

    def getAllPlaylists(self):
        offset = 0
        playlist = self.sp.current_user_playlists()
        nxt= playlist['next']
        all_playlists = playlist['items']
        while nxt != None:
            offset += 50 
            playlist = self.sp.current_user_playlists(offset=offset)
            nxt= playlist['next']
            all_playlists.extend(playlist['items'])
        return all_playlists

    def downloadSongs(self,songs : list,playlistName : str):

        playlist = m3uFile(playlistName)

        path = self.saveLocation+'/'+self.uid
        if not os.path.isdir(path):
            os.mkdir(path)

        if self.useDb:
            for i in songs:
                artists = ', '.join([x['name'] for x in i['track']['artists']])

                
                if not self.dbHelper.isNew(self.uid,i['track']['id']):
                    savedData = self.dbHelper.getData(self.uid,i['track']['id'])
                    playlist.addSong(str(savedData),i['track']['name'],artists)
                    continue
                
                thumb = getThumbnail(i['track'])
                downloadThumb(thumb,i['track']['id'])

                searchQuery = i['track']['name']+' by '+artists
                savedas = downloadSong(getYoutubeUrl(searchQuery),i['track']['name'],path)

                retryIfFailed = 3
                while retryIfFailed >= 0 and (not os.path.isfile(savedas)) :
                    savedas = downloadSong(getYoutubeUrl(searchQuery),i['track']['name'],path)
                    retryIfFailed -= 1
                    time.sleep(.5)

                if os.path.isfile(savedas):
                    convert_and_split(savedas)
                    addImage('.'.join(savedas.split('.')[:-1])+'.mp3','thumb/'+i['track']['id']+'.jpeg',i['track']['name'],artists)

                    t = getTime(path+'/'+i['track']['name']+'.mp3')
                    playlist.addSong(t,i['track']['name'],artists)

                    self.dbHelper.insertData(self.uid,i['track']['id'],t)
            
        else:
            path += ('/'+playlistName.replace('/',''))
            if not os.path.isdir(path):
                os.mkdir(path)
            for i in songs:
                artists = ', '.join([x['name'] for x in i['track']['artists']])
                
                thumb = getThumbnail(i['track'])
                downloadThumb(thumb,i['track']['id'])

                searchQuery = i['track']['name']+' by '+artists
                savedas = downloadSong(getYoutubeUrl(searchQuery),i['track']['name'],path)

                retryIfFailed = 3
                while retryIfFailed >= 0 and (not os.path.isfile(savedas)) :
                    savedas = downloadSong(getYoutubeUrl(searchQuery),i['track']['name'],path)
                    retryIfFailed -= 1
                    time.sleep(.5)

                if os.path.isfile(savedas):
                    convert_and_split(savedas)
                    addImage('.'.join(savedas.split('.')[:-1])+'.mp3','thumb/'+i['track']['id']+'.jpeg',i['track']['name'],artists)

                    t = getTime(path+'/'+i['track']['name']+'.mp3')
                    playlist.addSong(t,i['track']['name'],artists)

        playlist.createPlaylistFile()


    def changeUser(self):
        """
            Removes current user from cache, calls login again.
            !MAKE SURE THE CURRENT USER IS LOGGED OUT IN THE BROWSER BEFORE CALLING THIS FUNCTION!
        """
        if os.path.isfile('.cache'):
            os.remove('.cache')
        self.login()

    def __print_menu(self):
        self.printer.blanks('-').show()
        self.printer.text('1. Download Saved Songs').bold().show()
        self.printer.text('2. Download A Playlist').bold().show()
        self.printer.text('3. Change User ').bold().show()
        self.printer.text('4. Exit ').bold().show()
        self.printer.blanks('-').show()
        ch = int(input("Enter Your Choice: "))
        while ch<=0 and ch>4:
            self.printer.text("Invalid Choice!").center().bold().red().show()
            ch = int(input("Enter Your Choice: "))
        return ch
        


    def greet(self):
        """
            Greets the current user
        """
        self.printer.blanks('-').show()
        self.printer.text('Hi \U0001F44B '+self.name).center().bold().show()
        

    def run(self):
        """
            Interactive Terminal driver for downloading
        """
        self.login()
        self.greet()
        while True:
            ch = self.__print_menu()

            if ch == 1:
                songs = self.getAllSavedSongs()
                self.downloadSongs(songs,'Saved/Liked')
            
            if ch == 2:
                all_playlists = self.getAllPlaylists()
                k = 1
                for i in all_playlists:
                    print(str(k)+': '+i['name'])
                    print()
                    k+=1
                choice = int(input("Select Playlist to download:"))
                play = self.sp.playlist(all_playlists[choice-1]['id'])
                self.downloadSongs(play['tracks']['items'],play['name'])
            
            if ch == 3:
                self.changeUser()
                self.greet()

            if ch == 4:
                exit()

    def __del__(self):
        if(self.dbHelper != None):
            self.dbHelper.close()



    

if __name__ == "__main__":
    SpotifyDl().run()