import pylast
import os.path
import json
import collections

# Place one API key per line in keys.txt file in same directory
KEYS = []
START_USER = "RJ"
RUNNING = True
MAX_TRACKS = 50000  # Stop fetching user's tracks after this amount


def get_api_keys():
    with open("keys.txt") as file:
        for line in file:
            KEYS.append(line)


# Get last line of saved file and extract timestamp
# Done this way much faster on large files than reading line by line
def get_last_timestamp(path):
    with open(path, 'rb') as f:
        try:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)  # One-line file
        last_line = f.readline().decode()
    try:
        loaded = json.loads(last_line)
        if 'timestamp' in loaded:
            return loaded['timestamp']
    except ValueError:
        return 0


# Get amount of lines in a file. Uses buffer for much faster read
def get_line_count(path):
    def _make_gen(reader):
        while True:
            b = reader(2 ** 16)
            if not b:
                break
            yield b

    with open(path, 'rb') as f:
        count = sum(buf.count(b'\n') for buf in _make_gen(f.raw.read))
    return count


def save_tracks(user):
    username = user.name
    os.makedirs('saved', exist_ok=True)
    path = os.path.join('saved', username + '.json')

    track_count = 0
    timestamp = 0
    total = user.get_playcount()

    # If already saved, continue from last timestamp
    if os.path.exists(path):
        track_count = get_line_count(path)
        if track_count >= MAX_TRACKS:
            print(f"Reached max tracks {MAX_TRACKS}/{total} for {username}, stopping...")
            return

        timestamp = get_last_timestamp(path)
        print(f'File for {username} already exists, continuing from {track_count}/{total}')

    with open(path, 'a') as file:
        # Stream directly to file as we get the data
        for played_track in user.get_recent_tracks(limit=None, stream=True, time_to=timestamp):
            track = played_track.track
            # We can also get_top_artists, albums and tracks for any given tag
            # But we wouldn't want to get these on every single listened track

            # Get the top tags associated with this track
            # Sometimes tracks no longer exist so we only try a few times
            tries = 0
            top_tags_response = None
            while tries < 3:
                try:
                    top_tags_response = track.get_top_tags()
                    break
                except Exception as e:
                    print(f'Exception getting tags, trying again... {e}')
                    tries += 1
                    continue

            # Skip this track if we can't get the tags
            if top_tags_response is None:
                continue

            top_tags = []
            for top_item, weight in top_tags_response:
                top_tags.append({
                    'name': top_item.name,
                    'weight': weight
                })

            data = dict(
                title=track.title,
                mbid=played_track.track_mbid,
                artist={'name': track.artist.name, 'mbid': played_track.artist_mbid},
                top_tags=top_tags,
                album={'name': played_track.album, 'mbid': played_track.album_mbid},
                timestamp=played_track.timestamp,
            )
            dumped = json.dumps(data, separators=(',', ':'))
            file.write(dumped + '\n')
            track_count += 1
            print(f'Saved {track_count}/{total} tracks for {username}', end='\r')
            if track_count >= MAX_TRACKS:
                print(f"Reached max tracks {MAX_TRACKS} for {username}, stopping...")
                break

        print(f'Saved {track_count}/{total} tracks for {username}')


# Keep saving friends' track
# Friends is list of users to start off from
def friend_loop(friends):
    while RUNNING:
        print(f'Friends count: {len(friends)}')
        fof = set()  # Use set to avoid duplicates
        for friend in friends:
            tries = 0
            while tries < 5:
                try:
                    save_tracks(friend)
                    fof.update(friend.get_friends(limit=None))
                    print(f"Now have {len(fof)} friends")
                    break
                except KeyboardInterrupt:
                    print("Interrupt detected, stopping...")
                    return
                except Exception as e:
                    print(f'Exception, trying again... {e}')
                    tries += 1
                    continue

        friends = fof
        save_continue_list(friends)  # Save just in case program crashes or we stop it


# Get list of users to continue from
def get_continue_list(network):
    users = []
    if os.path.exists("continue.txt"):
        with open("continue.txt") as file:
            for line in file:
                # Make sure to remove newline char
                users.append(network.get_user(line[:-1]))
    return users


def save_continue_list(users):
    with open("continue.txt", 'w') as file:
        for user in users:
            file.write(f'{user.name}\n')


# Reimplementing pylast's function to also extract mbids
# This avoids making extra API calls
def _extract_played_track(self, track_node):
    title = pylast._extract(track_node, "name")
    track_mbid = pylast._extract(track_node, "mbid")
    track_artist = pylast._extract(track_node, "artist")
    artist_mbid = track_node.getElementsByTagName("artist")[0].getAttribute("mbid")
    date = pylast._extract(track_node, "date")
    album = pylast._extract(track_node, "album")
    album_mbid = track_node.getElementsByTagName("album")[0].getAttribute("mbid")
    timestamp = track_node.getElementsByTagName("date")[0].getAttribute("uts")
    return pylast.PlayedTrack(
        pylast.Track(track_artist, title, self.network),
        album, date, timestamp, track_mbid, artist_mbid, album_mbid
    )


def main():
    get_api_keys()
    network = pylast.LastFMNetwork(api_key=KEYS[0])
    network.enable_caching()

    # Override pylast's methods to get mbids
    pylast.PlayedTrack = collections.namedtuple(
        "PlayedTrack", ["track", "album", "playback_date", "timestamp", "track_mbid", "artist_mbid", "album_mbid"]
    )
    pylast.User._extract_played_track = _extract_played_track

    # Continue from where we left off, or start over
    continue_list = get_continue_list(network)
    if len(continue_list) <= 0:
        user = network.get_user(START_USER)
        continue_list = [user]

    friend_loop(continue_list)


if __name__ == "__main__":
    main()
