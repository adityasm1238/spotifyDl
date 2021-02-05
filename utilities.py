from youtube_search import YoutubeSearch
import json
import pafy
import time
import shutil
import requests
import subprocess
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error,TIT2,TPE1,TALB

def convert_and_split(filename):
    command = ['ffmpeg', '-i', filename,  '.'.join(filename.split('.')[:-1])+'.mp3']
    subprocess.run(command,stdout=None,stdin=subprocess.PIPE)
    os.remove(filename)

def downloadSong(url,name,location):
    vid = pafy.new('https://www.youtube.com'+url)
    a = vid.getbestaudio()
    a.download(filepath=location+'/'+name+"."+a.extension)
    return location+'/'+name+"."+a.extension

def createPlaylist(name):
    if(not os.path.isdir('songs/'+name)):
        os.mkdir('songs/'+name)

def getYoutubeUrl(name):
    try:
        results = YoutubeSearch(name, max_results=1).to_json()
    except:
        time.sleep(1)
        results = YoutubeSearch(name, max_results=1).to_json()
    return json.loads(results)['videos'][0]['url_suffix']

def addImage(song,image,name,artist):
    try:
        audio = MP3(song, ID3=ID3)
        try:
            audio.add_tags()
        except error:
            pass
        audio.tags.add(APIC(mime='image/jpeg',type=3,desc=u'Cover'+song,data=open(image,'rb').read()))
        audio.tags.add(TIT2(encoding=3, text=u""+name)) 
        audio.tags.add(TPE1(encoding=3, text=u""+artist)) 
        audio.tags.add(TALB(encoding=3, text=u""+name))
        audio.save() 
    except:
        pass
    os.remove(image)
def getThumbnail(song):
    im = song['album']['images']
    for i in im:
        if i['height'] == 300:
            return i['url']
    for i in im:
        if i['height'] == 640:
            return i['url']

def downloadThumb(url,id_):
    try:
        headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',}
        re = requests.get(url, stream = True,headers=headers)
        if re.status_code == 200:
            re.raw.decode_content = True
            destination = "thumb/"+id_+"."+"jpeg"
            with open(destination,'wb') as fi:
                shutil.copyfileobj(re.raw, fi)
    except:
        pass

def getTime(path):
    audio = MP3(path)
    return str(int(float(audio.info.length)*1000))


class m3uFile:
    def __init__(self,filename):
        self.lines = ['#EXTM3U\n']
        self.filename = filename
    
    def addSong(self,time,name,artists):
        self.lines.append('#EXTINF:'+time+','+artists+' - '+name+'\n')
        self.lines.append('/storage/emulated/0/spotifyoffline/'+name+'.mp3\n')
    
    def createPlaylistFile(self,dirr='playlists'):
        if not os.path.isdir(dirr):
            os.mkdir(dirr)
        with open(dirr+'/'+self.filename+'.m3u','w') as f:
            f.writelines(self.lines)