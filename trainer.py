import pickle
import os
import json
import re
import time
import csv
import random
import itertools
from scipy.sparse import csr_array

from sklearn.neighbors import NearestNeighbors

# Load up training data, train model and save it

LABELS_PATH = "labels.csv"  # Save the found labels for prediction time
INDEX_PATH = "index.csv"  # Save indices of training tracks for prediction time
MODEL_NAME = "model.sav"
SAVED_PATH = "saved"
BASELINES_PATH = "baselines"
TEST_DATA_TRACKS = 100
QUERY_TRACKS = 10
METRICS = ['l1', 'manhattan', 'cityblock', 'cosine', 'l2', 'euclidean']


# Process user listened tracks
def process_data():
    # Have to use dict instead of set because it's sorted
    found_labels = dict()  # Store all unique occurrences of each tag, artist name, album name
    unique_tracks = set()  # Set of tuples (artist, title) to avoid duplicates
    unique_artists = set()  # Set of tuples (artist, title) to avoid duplicates
    played_tracks_tags = []
    played_tracks_by_user = dict()  # Dict where keys are usernames and value lists of their played tracks
    query_tracks = dict()


    start_time_total = time.time()

    # Get training data from user files
    for filename in os.listdir(SAVED_PATH):
        filepath = os.path.join(SAVED_PATH, filename)
        if os.path.isfile(filepath):
            with open(filepath, encoding="utf8") as file:
                user_time = time.time()
                username = filename.replace(".json", '')
                played_tracks_user = list()
                print(f'Processing data for {username}')
                line_count = -1
                # Use most recent tracks as test data
                for line in file:
                    line_count += 1
                    played_track = None
                    if line_count <= QUERY_TRACKS:
                        if username not in query_tracks:
                            query_tracks[username] = list()
                        played_track = json.loads(line)
                        query_tracks[username].append(played_track)
                    elif line_count <= TEST_DATA_TRACKS:
                        continue

                    played_track = json.loads(line)
                    top_tags = played_track['top_tags']
                    artist_name = played_track['artist']['name']
                    album_name = played_track['album']['name']
                    title = played_track['title']

                    # Avoid duplicate tracks
                    if (artist_name, title) in unique_tracks:
                        continue
                    else:
                        unique_tracks.add((artist_name, title))

                    unique_artists.add(artist_name)

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
                    played_tracks_tags.append({'user': username, 'index': line_count, 'labels': filtered_labels})
                    played_tracks_user.append(played_track)

            played_tracks_by_user[username] = played_tracks_user
            user_taken = time.time() - user_time
            print(f'Processed {line_count} lines in {user_taken}')

    total_taken = time.time() - start_time_total
    print(f'Took {total_taken} to process all files')

    # Print stats
    print(f'Total labels: {len(found_labels)}')
    print(f'Unique tracks: {len(unique_tracks)}')
    print(f'Unique tracks: {len(unique_artists)}')
    print(f'Amount of users: {len(played_tracks_by_user)}')

    print("Saving labels...")
    save_labels(list(found_labels.keys()))
    print("Saving index...")
    save_index(played_tracks_tags)
    print("Calculating baselines...")
    calculate_baselines(played_tracks_by_user, query_tracks)
    print('Loading into matrix...')
    start_time = time.time()
    df = put_into_matrix(found_labels, played_tracks_tags)
    time_taken = time.time() - start_time
    print(f"Time taken: {time_taken}")
    return df


def baseline_most_common(played_tracks):
    occurrences = dict()
    for track in played_tracks:
        name = track['title'] + "_" + track['artist']['name']
        count = occurrences[name][0] if name in occurrences else 0
        occurrences[name] = (count + 1, track)
    # Sort tracks by occurences
    descending = sorted(occurrences.items(), key=lambda x: x[1][0], reverse=True)[:90]
    return_list = []
    for item in descending:
        return_list.append(item[1][1])
    return return_list


def baseline_most_recent(played_tracks):
    return played_tracks[:90]


def baseline_random(played_tracks):
    amount = 90 if len(played_tracks) > 90 else len(played_tracks)
    return random.choices(played_tracks, k=amount)


def save_baseline(username, baseline, predicted_tracks):
    with open(os.path.join(BASELINES_PATH, f'{username}_{baseline}.json'), "w", encoding="utf8") as file:
        for track in predicted_tracks:
            file.write(json.dumps(track, separators=(',', ':')) + "\n")


def baseline_artist_most_common(played_tracks, artist):
    occurrences = dict()
    for track in played_tracks:
        if track['artist']['name'] == artist:
            name = track['title'] + "_" + track['artist']['name']
            count = occurrences[name][0] if name in occurrences else 0
            occurrences[name] = (count + 1, track)
    # Sort tracks by occurences
    descending = sorted(occurrences.items(), key=lambda x: x[1][0], reverse=True)[:9]
    return_list = []
    for item in descending:
        return_list.append(item[1][1])
    return return_list


def baseline_tag_most_common(played_tracks, tag):
    occurrences = dict()
    for track in played_tracks:
        for tag_yoke in track['top_tags']:
            if tag == tag_yoke['name']:
                name = track['title'] + "_" + track['artist']['name']
                count = occurrences[name][0] if name in occurrences else 0
                occurrences[name] = (count + 1, track)
                break
    # Sort tracks by occurences
    descending = sorted(occurrences.items(), key=lambda x: x[1][0], reverse=True)[:9]
    return_list = []
    for item in descending:
        return_list.append(item[1][1])
    return return_list


def calculate_baselines(played_tracks_by_user: dict, query_tracks: dict):
    all_tracks = list(itertools.chain(*played_tracks_by_user.values()))
    overall_most_common = baseline_most_common(all_tracks)
    save_baseline("ALL_USERS", "most_common", overall_most_common)
    for username, played_tracks in played_tracks_by_user.items():
        user_most_common = baseline_most_common(played_tracks)
        save_baseline(username, "most_common", user_most_common)

        most_recent = baseline_most_recent(played_tracks)
        save_baseline(username, "most_recent", most_recent)

        user_random = baseline_random(played_tracks)
        save_baseline(username, "random", user_random)

        # Predictions based off of query tracks
        artists_most_common = list()
        tags_most_common = list()
        for query_track in query_tracks[username]:
            artists_most_common += baseline_artist_most_common(all_tracks, query_track['artist']['name'])
            top_tag = query_track['top_tags'][0]['name'] if len(query_track['top_tags']) > 0 else ''
            tags_most_common += baseline_tag_most_common(all_tracks, top_tag)
        save_baseline(username, "artist_most_common", artists_most_common)
        save_baseline(username, "tag_most_common", tags_most_common)


# Save list of labels to csv
def save_labels(labels):
    with open(LABELS_PATH, "w", encoding="utf8", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(labels)


# Get list of played tracks and save index of user and row
def save_index(played_tracks):
    with open(INDEX_PATH, "w", encoding="utf8", newline='') as file:
        writer = csv.writer(file)
        for track in played_tracks:
            user = track['user']
            index = track['index']  # Row in the user file where this played track is
            writer.writerow([user, index])


def put_into_matrix(found_labels, played_tracks):
    if None in found_labels:
        del found_labels[None]

    column_headers = found_labels.keys()

    row_indices = []
    col_indices = []
    data = []
    # Matrix should be len(played_tracks) * len(column_headers)

    # Make sparse array
    for row_index, played_track in enumerate(played_tracks):
        track_labels = played_track['labels']
        for col_index, label in enumerate(column_headers):
            if label in track_labels:
                data.append(1)
                row_indices.append(row_index)
                col_indices.append(col_index)

    print("Creating sparse array...")

    sparr = csr_array((data, (row_indices, col_indices)),
                      shape=(len(played_tracks), len(column_headers)),
                      dtype=int)

    return sparr


# Take in dataframe and return trained model
def train_models(df):
    for metric in METRICS:
        print(f"Training model with {metric} metric...")
        # Similarity between each played track and every other played track, shape df rows x df rows
        model = NearestNeighbors(algorithm='brute', metric=metric, n_jobs=-1).fit(X=df)
        print("Model trained")
        pickle.dump(model, open(f'{metric}_{MODEL_NAME}', 'wb'))
        print(f"Model saved to {metric}_{MODEL_NAME}")


def main():
    os.makedirs(SAVED_PATH, exist_ok=True)
    os.makedirs(BASELINES_PATH, exist_ok=True)
    print("Loading data...")
    df = process_data()
    print(f"Data loaded into dataframe of shape {df.shape}")
    train_models(df)


if __name__ == "__main__":
    main()
