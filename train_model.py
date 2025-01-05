import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import joblib

def train_model():
    # Load the preprocessed data
    X_train = np.load("X_train.npy")
    X_test = np.load("X_test.npy")
    y_train = np.load("y_train.npy")
    y_test = np.load("y_test.npy")

    # Step 1: Define the model (start with a Random Forest Regressor)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    # Step 2: Train the model
    model.fit(X_train, y_train)

    # Step 3: Evaluate the model
    y_pred = model.predict(X_test)
    print("Evaluation Metrics:")
    # MAE measures average magnitude of errors between 
    # predicted and actual values 
    # how far predictions are from actual values on average 
    # lower the better

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("Evaluation Metrics:")
    print(f"Mean Absolute Error (MAE): {mae:.2f}")
    print(f"Mean Squared Error (MSE): {mse:.2f}")
    print(f"R-squared (R²): {r2:.2f}")

    # Step 4: Save the trained model
    joblib.dump(model, "trained_model.pkl")
    print("Model saved to 'trained_model.pkl'.")

if __name__ == "__main__":
    train_model()
