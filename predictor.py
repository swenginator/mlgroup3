import os
import pandas
import numpy
import pickle
import json
import re
import time
import csv

LABELS_PATH = "labels.csv"
INDEX_PATH = "index.csv"  # Indices of training tracks
SAVED_PATH = "saved"
TEST_DATA_TRACKS = 100
QUERY_TRACKS = 10
MODEL_NAME = "model.sav"


# Get query tracks and "future" tracks
# e.g. use 10 test tracks to predict next 90 and compare
# Returns dataframe, query tracks, and list of future tracks
def load_test_data():
    # Have to use dict instead of set because it's sorted
    found_labels = load_labels()
    query_track_labels = []  # Tracks to predict from
    query_tracks = list()  # List of tuples (username, query track)
    future_tracks = dict()  # Keys are usernames, and values list of tracks to compare predictions to

    start_time_total = time.time()

    # Get test data from user files
    for filename in os.listdir(SAVED_PATH):
        filepath = os.path.join(SAVED_PATH, filename)
        if os.path.isfile(filepath):
            with open(filepath, encoding="utf8") as file:
                user_time = time.time()
                username = filename.replace(".json", '')
                print(f'Processing data for {username}')
                line_count = 0
                # Use most recent tracks as test data
                for line in file:
                    line_count += 1
                    if line_count > TEST_DATA_TRACKS:  # Training data, ignore
                        break
                    played_track = json.loads(line)
                    if line_count > QUERY_TRACKS:  # Future tracks
                        if username not in future_tracks:
                            future_tracks[username] = list()
                        future_tracks[username].append(played_track)
                        continue
                    else:
                        query_tracks.append((username, played_track))

                    # Remaining tracks are query tracks to predict from
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
                    query_track_labels.append(filtered_labels)

            user_taken = time.time() - user_time
            print(f'Processed {line_count} lines in {user_taken}')

    total_taken = time.time() - start_time_total
    print(f'Took {total_taken} to process all files')
    print('Loading into dataframe...')
    start_time = time.time()
    df = put_into_dataframe(found_labels, query_track_labels)
    time_taken = time.time() - start_time
    print(f"Time taken: {time_taken}")
    return df, query_tracks, future_tracks


# Return specified track object
def get_track(username: str, linenum: int):
    # Open up specified user file
    with open(os.path.join(SAVED_PATH, f'{username}.json'), encoding="utf8") as file:
        index = 0
        for line in file:
            if index < linenum:
                index += 1
            else:
                return json.loads(line)


# Index is list of tuples of (username, linenum)
def load_index():
    index = list()
    with open(INDEX_PATH, encoding="utf8", newline='') as csvfile:
        for row in csv.reader(csvfile):
            row_tuple = ()
            for item in row:
                row_tuple += (item,)
            index.append(row_tuple)
    return index


def load_labels():
    labels = dict()
    with open(LABELS_PATH, encoding="utf8", newline='') as csvfile:
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


# Returns dict where keys are usernames, values list of tuples of (query, list(predictions))
def predict_model(model):
    track_index = load_index()
    df, query_tracks, future_tracks = load_test_data()
    # For every 10 query tracks we have 90 future tracks, so predict 9 neighbours for each
    predictions = model.kneighbors(X=df, n_neighbors=9, return_distance=False)

    query_count = 0
    results = dict()  # Keys are usernames, values are result class
    for query in predictions:
        predicted_tracks = list()  # This will be predictions for a single query
        for predicted_track_index in query:
            username, linenum = track_index[predicted_track_index]
            predicted_track = get_track(username, int(linenum))
            predicted_tracks.append(predicted_track)

        username, query_track = query_tracks[query_count]
        if username not in results:
            results[username] = Result()
        result = results[username]
        result.query_tracks.append(query_track)
        result.predicted_tracks.append(predicted_tracks)
        result.future_tracks = future_tracks

        query_count += 1

    return results


class Result:
    future_tracks: list  # The most recent of the user's tracks
    query_tracks: list  # The 10 least recent of the test tracks
    predicted_tracks: list  # The 90 tracks predicted from the query tracks as lists of 10

    def __init__(self):
        self.future_tracks = list()
        self.query_tracks = list()
        self.predicted_tracks = list()


def main():
    loaded_model = pickle.load(open(MODEL_NAME, 'rb'))
    results = predict_model(loaded_model)

    for username, result in results.items():
        future_tracks = result.future_tracks
        for i in range(len(result.query_tracks)):
            query = result.query_tracks[i]
            print(f"Query track from {username}:")
            print(f"{query['artist']['name']} - {query['title']}")
            print("Predicted tracks:")
            for prediction in result.predicted_tracks[i]:
                print(f"{prediction['artist']['name']} - {prediction['title']}")
            print()

        print()
        print()


if __name__ == "__main__":
    main()
