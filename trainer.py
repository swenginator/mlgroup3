import pandas
import numpy

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

CSV_PATH = "playedtracks.csv"


# Take in dataframe and return trained model
def train_model(df):
    print("Training model...")
    data_similarity = cosine_similarity(df.T)
    print(data_similarity)
    data_similarity_df = pandas.DataFrame(data_similarity, columns=df.columns, index=df.columns)
    neigh = NearestNeighbors(n_neighbors=len(df.columns)).fit(data_similarity_df)
    model = pandas.DataFrame(neigh.kneighbors(data_similarity_df, return_distance=False))

    return pandas.DataFrame(data_similarity_df.columns[model], index=data_similarity_df.index)

# Take in trained model and last few played tracks for specific user
# and predict most likely tracks
def make_prediction(model, played_tracks):
    print("Predicting...")
    # TODO predict and just print out top ten for now


def main():
    df = pandas.read_csv(CSV_PATH, dtype=numpy.uint8)
    print(f"Data loaded into dataframe of shape {df.shape}")
    breakpoint()
    model = train_model(df)
    print(f"Model trained, intercept: {model.intercept_}, coefs: {model.coef_}")


if __name__ == "__main__":
    main()
