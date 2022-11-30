import os
import json
import re

SAVED_PATH = "saved"
OUTPUT_NAME = "playedtracks.csv"

# Process user listened tracks and saves data into csv
# Have to use dict instead of set because it's sorted
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

                filtered_labels = []
                if artist_name is not None and len(artist_name) > 0:
                    artist_name = artist_name.replace(',', '')
                    filtered_labels.append(artist_name)
                    found_labels[artist_name] = None
                if album_name is not None and len(album_name) > 0:
                    album_name = album_name.replace(',', '')
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
                    name = name.replace('-', '').replace(',', '').lower()
                    weight = int(label['weight'])
                    if len(re.findall(r'\d+', name)) <= 0 and weight > 50:
                        filtered_labels.append(name)
                        found_labels[name] = None
                        count += 1

                # Add tags to list of played tracks
                played_tracks.append(filtered_labels)

with open(OUTPUT_NAME, "w") as file:
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
