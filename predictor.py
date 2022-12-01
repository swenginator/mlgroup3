import pickle
import os
import pandas
import numpy
import pickle
import json
import re
import time
import csv

from sklearn.neighbors import NearestNeighbors

CSV_PATH = "labels.csv"
SAVED_PATH = "saved"
TEST_DATA_TRACKS = 100
MODEL_NAME = "model.sav"


# Process user listened tracks
def load_test_data():
    # Have to use dict instead of set because it's sorted
    found_labels = load_labels()
    played_tracks = []

    start_time_total = time.time()

    # Get test data from user files
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
                    if line_count > 100:
                        break
                    played_track = json.loads(line)
                    top_tags = played_track['top_tags']
                    artist_name = played_track['artist']['name']
                    album_name = played_track['album']['name']

                    filtered_labels = []
                    if artist_name is not None and len(artist_name) > 0:
                        artist_name = "artist_" + artist_name.replace(',', '')
                        filtered_labels.append(artist_name)
                    if album_name is not None and len(album_name) > 0:
                        album_name = "album_" + album_name.replace(',', '')
                        filtered_labels.append(album_name)

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
                            count += 1

                    # Add tags to list of played tracks
                    played_tracks.append(filtered_labels)

            user_taken = time.time() - user_time
            print(f'Processed {line_count} lines in {user_taken}')
        break  # Do with only one user

    total_taken = time.time() - start_time_total
    print(f'Took {total_taken} to process all files')
    print('Loading into dataframe...')
    start_time = time.time()
    df = put_into_dataframe(found_labels, played_tracks)
    time_taken = time.time() - start_time
    print(f"Time taken: {time_taken}")
    return df


def load_labels():
    labels = dict()
    with open(CSV_PATH) as csvfile:
        for row in csv.reader(csvfile):
            for label in row:
                labels[label] = None
            break  # Only one row of labels
    return labels


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


def predict_model(model):
    df = load_test_data()
    predictions = model.kneighbors(X=df, n_neighbors=15, return_distance=False)
    for indices in predictions:
        for i in indices:
            print(df.columns[i])


def main():
    loaded_model = pickle.load(open(MODEL_NAME, 'rb'))
    predict_model(loaded_model)


if __name__ == "__main__":
    main()
