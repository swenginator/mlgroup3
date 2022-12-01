import pandas
import numpy
import pickle

from sklearn.neighbors import NearestNeighbors

CSV_PATH = "playedtracks.csv"
MODEL_NAME = "model.sav"


# Take in dataframe and return trained model
def train_model(df):
    print("Training model...")
    # Similarity between each played track and every other played track, shape df rows x df rows
    neigh = NearestNeighbors(n_neighbors=len(df.index), algorithm='brute', metric='cosine').fit(X=df)
    # TODO make prediction on the test data not the training data
    predictions = neigh.kneighbors(X=df.iloc[:1], n_neighbors=15, return_distance=False)
    for indices in predictions:
        for i in indices:
            print(df.columns[i])

    return neigh


def main():
    df = pandas.read_csv(CSV_PATH, dtype=numpy.uint8)
    print(f"Data loaded into dataframe of shape {df.shape}")
    model = train_model(df)
    print("Model trained")
    pickle.dump(model, open(MODEL_NAME, 'wb'))
    print(f"Model saved to {MODEL_NAME}")


if __name__ == "__main__":
    main()
