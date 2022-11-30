import os
import json
import pandas
import re
import numpy

SAVED_PATH = "saved"


# Returns dataframe with each row as playedsong and columns with name of each tag
def load_into_pandas():
    for filename in os.listdir(SAVED_PATH):
        print(filename)
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
                        if count > 0:  # Only get top tag
                            break
                        name = tag['name'].replace('-', '').lower()
                        weight = int(tag['weight'])
                        if len(re.findall(r'\d+', name)) <= 0 and weight > 50:
                            filtered_tags.append(name)
                            found_tags[name] = None
                            count += 1

                    # Add tags to list of played tracks
                    played_tracks.append({
                        'title': played_track['title'],
                        'artist': played_track['artist']['name'],
                        'album': played_track['album']['name'],
                        'tags': filtered_tags})

            break  # For now only go through one user

            # df = pandas.DataFrame(track_dict)
            # print(df)
            # each row is a recorded track
            # each column is a tag

    # print("Found tags:")
    # print(found_tags)

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
    return df


# Take in dataframe and return trained model
def train_model(df):
    print("Training model...")
    # TODO


# Take in trained model and last few played tracks for specific user
# and predict most likely tracks
def make_prediction(model, played_tracks):
    print("Predicting...")
    # TODO predict and just print out top ten for now


def main():
    df = load_into_pandas()
    breakpoint()


if __name__ == "__main__":
    main()
