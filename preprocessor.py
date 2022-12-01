import os
import json
import re

SAVED_PATH = "saved"
TEST_DATA_PATH = "test_data"
TRAIN_DATA_FILENAME = "playedtracks.csv"
TEST_DATA_TRACKS = 100


# Process user listened tracks and saves data into csv
def process_data():
    # Have to use dict instead of set because it's sorted
    found_labels = dict()  # Store all unique occurrences of each tag, artist name, album name
    played_tracks = []
    test_tracks = []

    # Get training data from user files
    for filename in os.listdir(SAVED_PATH):
        filepath = os.path.join(SAVED_PATH, filename)
        if os.path.isfile(filepath):
            with open(filepath) as file:
                username = filename.replace(".json", '')
                print(f'Processing data for {username}')
                line_count = 0
                # Use most recent tracks as test data
                for line in file:
                    line_count += 1
                    testing = line_count <= TEST_DATA_TRACKS
                    played_track = json.loads(line)
                    top_tags = played_track['top_tags']
                    artist_name = played_track['artist']['name']
                    album_name = played_track['album']['name']

                    filtered_labels = []
                    if artist_name is not None and len(artist_name) > 0:
                        artist_name = "artist_" + artist_name.replace(',', '')
                        filtered_labels.append(artist_name)
                        if not testing:
                            found_labels[artist_name] = None
                    if album_name is not None and len(album_name) > 0:
                        album_name = "album_" + album_name.replace(',', '')
                        filtered_labels.append(album_name)
                        if not testing:
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
                    if testing:
                        test_tracks.append(filtered_labels)
                    else:
                        played_tracks.append(filtered_labels)

            # Save test data for this user
            save_to_csv(os.path.join(TEST_DATA_PATH, f'{username}.csv'), found_labels, test_tracks)

    # Save training data
    save_to_csv(TRAIN_DATA_FILENAME, found_labels, played_tracks)


def save_to_csv(filename, found_labels, played_tracks):
    with open(filename, "w", encoding="utf8") as file:
        if None in found_labels:
            del found_labels[None]
        # Write column headers
        column_headers = list(found_labels)
        for i in range(len(column_headers) - 1):
            file.write(column_headers[i] + ',')

        file.write(column_headers[len(column_headers) - 1] + '\n')

        for played_track in played_tracks:
            row_values = list()
            for label in found_labels.keys():
                value = '1' if label in played_track else '0'
                row_values.append(value)

            for i in range(len(row_values) - 1):
                file.write(row_values[i] + ',')

            # Add last item in row without comma but with newline instead
            file.write(row_values[len(row_values) - 1] + '\n')


def main():
    os.makedirs(SAVED_PATH, exist_ok=True)  # Make data directory
    os.makedirs(TEST_DATA_PATH, exist_ok=True)  # Make test directory
    process_data()


if __name__ == "__main__":
    main()
