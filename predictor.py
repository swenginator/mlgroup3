import pickle
import os
import pandas
import numpy

from sklearn.neighbors import NearestNeighbors

CSV_PATH = "test_data"
MODEL_NAME = "KNN_model.sav"


def predict_model(model, df):
    for filename in os.listdir(CSV_PATH):
        filepath = os.path.join(CSV_PATH,filename)
        if os.path.exists(filepath):
            df = pandas.read_csv(filepath, dtype=numpy.uint8)
            neigh = NearestNeighbors(n_neighbors=len(df.index), algorithm='brute', metric='cosine').fit(X=df)
            
            predictions = neigh.kneighbors(X=df.iloc[:1], n_neighbors=15, return_distance=False)
            for indices in predictions:
                for i in indices:
                    print(df.columns[i])

def main():
    loaded_model = pickle.load(open(MODEL_NAME, 'rb'))
    predict_model(loaded_model)
    
if __name__ == "__main__":
    main()