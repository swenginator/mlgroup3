import os
import json
import pandas
import re

SAVED_PATH = "saved"


def load_into_pandas():
    for filename in os.listdir(SAVED_PATH):
        # Have to use dict instead of set cause it's sorted
        found_tags = dict()  # Store all unique occurrences of each tag
        played_tracks = []
        # check if current path is a file
        filepath = os.path.join(SAVED_PATH, filename)
        if os.path.isfile(filepath):
            with open(filepath) as file:
                for line in file:
                    played_track = json.loads(line)
                    top_tags = played_track['top_tags']
                    # Grab tag names and remove years
                    filtered_tags = []
                    count = 0
                    for tag in top_tags:
                        if count > 5:
                            break
                        name = tag['name'].replace('-', '').lower()
                        weight = int(tag['weight'])
                        if len(re.findall(r'\d+', name)) <= 0 and weight > 50:
                            filtered_tags.append(name)
                            found_tags[name] = None
                            count += 1

                    # Add tags to list of played tracks
                    played_tracks.append({
                        'timestamp': played_track['timestamp'],
                        'title': played_track['title'],
                        'artist': played_track['artist']['name'],
                        'album': played_track['album']['name'],
                        'tags': filtered_tags})

            break  # For now only go through one user

            # df = pandas.DataFrame(track_dict)
            # print(df)
            # each row is a recorded track
            # each column is a tag

    #print("Found tags:")
    #print(found_tags)

    # We need a dictionary where keys are tags and values are lists
    ligma = dict()
    for track in played_tracks:
        for tag in found_tags.keys():
            if tag not in ligma:
                ligma[tag] = list()
            taglist = ligma[tag]
            taglist.append(1 if tag in track['tags'] else 0)


    df = pandas.DataFrame(ligma)
    print(df)

    #print("Played tracks:")
    #[print(track) for track in played_tracks]


def main():
    load_into_pandas()


if __name__ == "__main__":
    main()
