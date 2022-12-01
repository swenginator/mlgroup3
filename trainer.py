import pandas
import numpy
import pickle
import os
import json
import re
import time

from sklearn.neighbors import NearestNeighbors

CSV_PATH = "labels.csv"
MODEL_NAME = "model.sav"
SAVED_PATH = "saved"
TEST_DATA_TRACKS = 100


# Process user listened tracks
def process_data():
    # Have to use dict instead of set because it's sorted
    found_labels = dict()  # Store all unique occurrences of each tag, artist name, album name
    played_tracks = []

    start_time_total = time.time()

    # Get training data from user files
    for filename in os.listdir(SAVED_PATH):
        filepath = os.path.join(SAVED_PATH, filename)
        if os.path.isfile(filepath):
            with open(filepath) as file:
                user_time = time.time()
                username = filename.replace(".json", '')
                print(f'Processing data for {username}')
                line_count = 0
                # Use most recent tracks as test data
                for line in file:
                    line_count += 1
                    if line_count <= 100:
                        continue
                    played_track = json.loads(line)
                    top_tags = played_track['top_tags']
                    artist_name = played_track['artist']['name']
                    album_name = played_track['album']['name']

                    filtered_labels = []
                    if artist_name is not None and len(artist_name) > 0:
                        artist_name = "artist_" + artist_name.replace(',', '')
                        filtered_labels.append(artist_name)
                        found_labels[artist_name] = None
                    if album_name is not None and len(album_name) > 0:
                        album_name = "album_" + album_name.replace(',', '')
                        filtered_labels.append(album_name)
                        found_labels[album_name] = None

                    # Grab tag names and remove years
                    count = 0
                    for label in top_tags:
                        if count > 5:  # Only get top 5 tags for each track
                            break
                        if label is None:
                            continue
                        name = label['name']
                        if name is None or len(name) < 0:
                            continue
                        name = "tag_" + name.replace('-', '').replace(',', '').lower()
                        weight = int(label['weight'])
                        if len(re.findall(r'\d+', name)) <= 0 and weight > 50:
                            filtered_labels.append(name)
                            found_labels[name] = None
                            count += 1

                    # Add tags to list of played tracks
                    played_tracks.append(filtered_labels)

            user_taken = time.time() - user_time
            print(f'Processed {line_count} lines in {user_taken}')

    total_taken = time.time() - start_time_total
    print(f'Took {total_taken} to process all files')
    print("Saving labels...")
    save_labels(list(found_labels.keys()))
    print('Loading into dataframe...')
    start_time = time.time()
    df = put_into_dataframe(found_labels, played_tracks)
    time_taken = time.time() - start_time
    print(f"Time taken: {time_taken}")
    return df


# Save list of labels to csv
def save_labels(labels):
    with open(CSV_PATH, "w") as file:
        for i in range(len(labels) - 1):
            file.write(labels[i] + ",")
        file.write(labels[-1] + '\n')


def put_into_dataframe(found_labels, played_tracks):
    if None in found_labels:
        del found_labels[None]

    column_headers = found_labels.keys()
    rows = list()

    # Make dense array
    for played_track in played_tracks:
        row = []
        for label in column_headers:
            row.append(1 if label in played_track else 0)

        # Make numpy array of indices where it's 1
        sparr = pandas.arrays.SparseArray(row, fill_value=0)
        del row
        rows.append(sparr)

    df = pandas.DataFrame(rows, columns=column_headers, dtype=numpy.uint8)
    return df


# Take in dataframe and return trained model
def train_model(df):
    print("Training model...")
    # Similarity between each played track and every other played track, shape df rows x df rows
    return NearestNeighbors(n_neighbors=len(df.index), algorithm='brute', metric='cosine').fit(X=df)


def main():
    print("Loading data...")
    df = process_data()
    print(f"Data loaded into dataframe of shape {df.shape}")
    model = train_model(df)
    print("Model trained")
    pickle.dump(model, open(MODEL_NAME, 'wb'))
    print(f"Model saved to {MODEL_NAME}")


if __name__ == "__main__":
    main()
