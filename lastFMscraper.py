import requests
import json
import time
import pandas as pd

def getFriends(n, user, listOfFriends):
    request_url = url1.format("friends", user, key, limit, extended, page)
    response = requests.get(request_url).json()
    for item in response["friends"]["user"]:
        if item not in listOfFriends:
            listOfFriends.append(item["name"])
    if n == 0:
        return listOfFriends
    else:
        for friend in listOfFriends:
            getFriends(n-1,friend, listOfFriends)
    return listOfFriends

def getSongs(user):
    method='toptracks'
    
    request_url = url.format(method, username, key, limit, extended)
    response = requests.get(request_url).json()
    pages = response[method]["@attr"]["totalPages"]
    for i in range(int(pages)):
        request_url = url.format(method, username, key, limit, extended, i)
        response = requests.get(request_url).json()

        allSongs = []

        f = open("UserSongList\\"+user+".txt","w")

        for item in response[method]["track"]:
            if item not in allSongs:
                f.write(item["name"]+", "+item["mbid"]+"\n")
        f.close()
        

pause_duration = 0.2
key = "b5dd048101c7fb6285afcb0398ec3e58"

username = "wlc2333"
username = "rj"
url1 = 'https://ws.audioscrobbler.com/2.0/?method=user.get{}&user={}&api_key={}&limit={}&extended={}&page={}&format=json'
url = 'https://ws.audioscrobbler.com/2.0/?method=user.get{}&user={}&api_key={}&limit={}&extended={}&format=json'



limit = 200; extended = 0; page = 1

sampleUsers = [username]
sampleUsers = getFriends(0, username, sampleUsers)
print(sampleUsers)
for i in sampleUsers:
    getSongs(i)
    print(i+" complete!")
