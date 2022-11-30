import os
import json
import pandas
import re
import numpy

SAVED_PATH = "saved"


# Returns dataframe with each row as playedsong and columns with name of each tag
def load_into_pandas():
    # Have to use dict instead of set cause it's sorted
    found_labels = dict()  # Store all unique occurrences of each tag, artist name, album name
    played_tracks = []

    for filename in os.listdir(SAVED_PATH):
        # check if current path is a file
        filepath = os.path.join(SAVED_PATH, filename)
        if os.path.isfile(filepath):
            with open(filepath) as file:
                print(f'User: {filename}')
                for line in file:
                    played_track = json.loads(line)
                    top_tags = played_track['top_tags']
                    artist_name = played_track['artist']['name']
                    album_name = played_track['album']['name']

                    filtered_labels = [artist_name, album_name]
                    found_labels[artist_name] = None
                    found_labels[album_name] = None

                    # Grab tag names and remove years
                    count = 0
                    for label in top_tags:
                        if count > 5:  # Only get top 5 tags for each track
                            break
                        name = label['name'].replace('-', '').lower()
                        weight = int(label['weight'])
                        if len(re.findall(r'\d+', name)) <= 0 and weight > 50:
                            filtered_labels.append(name)
                            found_labels[name] = None
                            count += 1

                    # Add tags to list of played tracks
                    played_tracks.append(filtered_labels)

            # df = pandas.DataFrame(track_dict)
            # print(df)
            # each row is a recorded track
            # each column is a tag

    # print("Found tags:")
    # print(found_tags)

    # We need a dictionary where keys are labels and values are lists
    df_dict = dict()
    for track in played_tracks:
        for label in found_labels.keys():
            if label not in df_dict:
                df_dict[label] = list()
            labellist = df_dict[label]
            labellist.append(1 if label in track else 0)

    df = pandas.DataFrame(df_dict)
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
    print(f"Data loaded into dataframe of shape {df.shape}")
    breakpoint()
    model = train_model(df)
    print(f"Model trained, intercept: {model.intercept_}, coefs: {model.coef_}")


if __name__ == "__main__":
    main()
