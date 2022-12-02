import os
import pickle
import json
import re
import time
import csv
from scipy.sparse import csr_array

LABELS_PATH = "labels.csv"
INDEX_PATH = "index.csv"  # Indices of training tracks
SAVED_PATH = "saved"
BASELINES_PATH = "baselines"
TEST_DATA_TRACKS = 100
QUERY_TRACKS = 10
MODEL_NAME = "model.sav"
METRICS = ['manhattan', 'cosine', 'euclidean']
BASELINES_TYPES = ["most_common", "most_recent", "random", "artist_most_common", "tag_most_common"]


# Get query tracks and "future" tracks
# e.g. use 10 test tracks to predict next 90 and compare
# Returns matrix, query tracks, and list of future tracks
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
                    if line_count <= TEST_DATA_TRACKS - QUERY_TRACKS:  # Future tracks
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
    print('Loading into matrix...')
    start_time = time.time()
    df = put_into_matrix(found_labels, query_track_labels)
    time_taken = time.time() - start_time
    print(f"Time taken: {time_taken}")
    return df, query_tracks, future_tracks


# Return specified track object
def get_track(username: str, linenum: int):
    # Open up specified user file
    with open(os.path.join(SAVED_PATH, f'{username}.json')) as file:
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


def load_baseline(username, baseline_type):
    predictions = list()
    # Chunk it up in lists of 9 each to match the queries
    with open(os.path.join(BASELINES_PATH, f'{username}_{baseline_type}.json'), encoding="utf8") as file:
        current_list = list()
        count = 0
        for line in file:
            track = json.loads(line)
            current_list.append(track)
            if count >= 8:
                predictions.append(current_list)
                current_list = list()
                count = 0
            else:
                count += 1
    return predictions


def put_into_matrix(found_labels, played_tracks):
    if None in found_labels:
        del found_labels[None]

    column_headers = found_labels.keys()

    row_indices = []
    col_indices = []
    data = []

    # Make sparse array
    for row_index, labels in enumerate(played_tracks):
        for col_index, label in enumerate(column_headers):
            if label in labels:
                data.append(1)
                row_indices.append(row_index)
                col_indices.append(col_index)

    print("Putting into sparse array...")
    sparr = csr_array((data, (row_indices, col_indices)),
                      shape=(len(played_tracks), len(column_headers)),
                      dtype=int)

    return sparr


def predict_model(model, df, query_tracks, future_tracks):
    track_index = load_index()
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
        result.future_tracks = future_tracks[username]

        query_count += 1

    return results


# Compares predicted tracks for a given user to what they actually listened to
def compare(result):
    averages = [0, 0, 0, 0]
    future_tacks = result.future_tracks
    predictions = result.predicted_tracks

    predicted_titles = set()
    predicted_artists = set()
    predicted_albums = set()
    predicted_tags = set()

    count = 0
    titles_correct = 0
    artists_correct = 0
    albums_correct = 0
    tags_correct = 0
    total_tags = 0

    for prediction in predictions:
        for predicted_track in prediction:
            predicted_titles.add(predicted_track['title'])
            predicted_artists.add(predicted_track['artist']['name'])
            predicted_albums.add(predicted_track['album']['name'])

            # Add top 5 tags
            counter = 0
            for tag in predicted_track['top_tags']:
                if count > 5:
                    break
                if int(tag['weight']) >= 50:
                    predicted_tags.add(tag['name'])
                    counter += 1

    for track in future_tacks:
        titles_correct += int(track['title'] in predicted_titles)
        artists_correct += int(track['artist']['name'] in predicted_artists)
        albums_correct += int(track['album']['name'] in predicted_albums)

        for tag in track['top_tags']:
            if int(tag['weight']) >= 50:
                total_tags += 1
                if tag['name'] in predicted_tags:
                    tags_correct += 1

        count += 1

    averages[0] += titles_correct / count
    averages[1] += artists_correct / count
    averages[2] += albums_correct / count
    averages[3] += tags_correct / total_tags

    return averages


class Result:
    future_tracks: list  # The most recent of the user's tracks
    query_tracks: list  # The 10 least recent of the test tracks
    predicted_tracks: list  # The 90 tracks predicted from the query tracks as lists of 10

    def __init__(self):
        self.future_tracks = list()
        self.query_tracks = list()
        self.predicted_tracks = list()


def main():
    # Make directories
    os.makedirs(SAVED_PATH, exist_ok=True)
    os.makedirs(BASELINES_PATH, exist_ok=True)

    df, query_tracks, future_tracks = load_test_data()

    all_averages = list()
    results = None
    for metric in METRICS:
        model_name = f'{metric}_{MODEL_NAME}'
        print(f"Predicting using {model_name}")
        loaded_model = pickle.load(open(model_name, 'rb'))
        results = predict_model(loaded_model, df, query_tracks, future_tracks)

        model_averages = [0, 0, 0, 0]
        count = 0
        for username, result in results.items():
            count += 1
            user_averages = compare(result)
            for i, ave in enumerate(user_averages):
                model_averages[i] += ave

        for i, ave in enumerate(model_averages):
            model_averages[i] /= count

        all_averages.append(model_averages)

        print(f"Overall Average for {model_name}")
        print("Title: {:.2%}".format(model_averages[0]))
        print("Artist: {:.2%}".format(model_averages[1]))
        print("Album: {:.2%}".format(model_averages[2]))
        print("Tags: {:.2%}".format(model_averages[3]))
        print('\n\n')

    for baseline_type in BASELINES_TYPES:
        baseline_averages = [0, 0, 0, 0]
        count = 0
        for username, result in results.items():
            baseline = load_baseline(username, baseline_type)
            result.predicted_tracks = baseline

            count += 1
            user_averages = compare(result)
            for i, ave in enumerate(user_averages):
                baseline_averages[i] += ave

            for i, ave in enumerate(baseline_averages):
                baseline_averages[i] /= count

        all_averages.append(baseline_averages)

    filtered_types = list()
    for baseline_type in BASELINES_TYPES:
        filtered_types.append(baseline_type.replace("_", " "))

    for metric, model_averages in zip((METRICS + filtered_types), all_averages):
        ave_string = ''.join(f' & {ave:.2}' for ave in model_averages)
        print(f'{metric}{ave_string}\\\\\n\\hline')


if __name__ == "__main__":
    main()
