import pandas
import numpy
import pickle

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

CSV_PATH = "playedtracks.csv"
MODEL_NAME = "model.sav"


# Take in dataframe and return trained model
def train_model(df):
    print("Training model...")
    data_similarity = cosine_similarity(df.T)
    print(data_similarity)
    data_similarity_df = pandas.DataFrame(data_similarity, columns=df.columns, index=df.columns)
    neigh = NearestNeighbors(n_neighbors=len(df.columns)).fit(data_similarity_df)
    model = pandas.DataFrame(neigh.kneighbors(data_similarity_df, return_distance=False))

    return pandas.DataFrame(data_similarity_df.columns[model], index=data_similarity_df.index)


def main():
    df = pandas.read_csv(CSV_PATH, dtype=numpy.uint8)
    print(f"Data loaded into dataframe of shape {df.shape}")
    model = train_model(df)
    print("Model trained")
    pickle.dump(model, open(MODEL_NAME, 'wb'))
    print(f"Model saved to {MODEL_NAME}")


if __name__ == "__main__":
    main()
