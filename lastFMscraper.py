import requests
import json


def get_friends(n, user, friends_list):
    request_url = url1.format("friends", user, key, limit, extended, page)
    response = requests.get(request_url).json()
    for item in response["friends"]["user"]:
        if item not in friends_list:
            friends_list.append(item["name"])
    if n == 0:
        return friends_list
    else:
        for friend in friends_list:
            get_friends(n - 1, friend, friends_list)
    return friends_list


def get_songs(user):
    method = 'toptracks'

    request_url = url.format(method, username, key, limit, extended)
    response = requests.get(request_url).json()
    pages = response[method]["@attr"]["totalPages"]
    for i in range(int(pages)):
        request_url = url.format(method, username, key, limit, extended, i)
        response = requests.get(request_url).json()

        allSongs = []

        f = open("UserSongList\\" + user + ".txt", "w")

        for item in response[method]["track"]:
            if item not in allSongs:
                f.write(item["name"] + ", " + item["mbid"] + "\n")
        f.close()


pause_duration = 0.2
key = "b5dd048101c7fb6285afcb0398ec3e58"

username = "wlc2333"
username = "rj"
url1 = 'https://ws.audioscrobbler.com/2.0/?method=user.get{}&user={}&api_key={}&limit={}&extended={}&page={}&format=json'
url = 'https://ws.audioscrobbler.com/2.0/?method=user.get{}&user={}&api_key={}&limit={}&extended={}&format=json'

limit = 200
extended = 0
page = 1

sampleUsers = [username]
sampleUsers = get_friends(0, username, sampleUsers)
print(sampleUsers)
for i in sampleUsers:
    get_songs(i)
    print(i + " complete!")
