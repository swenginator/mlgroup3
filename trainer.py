import pandas
import numpy

CSV_PATH = "playedtracks.csv"


# Take in dataframe and return trained model
def train_model(df):
    print("Training model...")
    # TODO


# Take in trained model and last few played tracks for specific user
# and predict most likely tracks
def make_prediction(model, played_tracks):
    print("Predicting...")
    # TODO predict and just print out top ten for now


def main():
    df = pandas.read_csv(CSV_PATH)
    print(f"Data loaded into dataframe of shape {df.shape}")
    model = train_model(df)
    print(f"Model trained, intercept: {model.intercept_}, coefs: {model.coef_}")


if __name__ == "__main__":
    main()
