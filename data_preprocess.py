import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np

def preprocess_data(file_path):
    """
    Preprocess the training data for model input.
    """
    # Load the data
    data = pd.read_csv(file_path)

    # Handle missing values (if any)
    data.fillna(0, inplace=True)

    # Feature engineering: Example features derived from existing data
    data["is_home_game"] = data["fixture_difficulty"] % 2 == 0  # Derived feature: Home game based on fixture difficulty
    
    # Feature scaling adjustments: Ensure numeric-only features are used
    numeric_features = ["recent_form", "team_strength_home", "team_strength_away", "fixture_difficulty", "gameweek"]
    X = data[numeric_features]

    # Define target variable (y)
    y = data["total_points"]  # Predicting total points for the next gameweek

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Scale the features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Save the preprocessed data
    np.save("X_train.npy", X_train_scaled)
    np.save("X_test.npy", X_test_scaled)
    np.save("y_train.npy", y_train.to_numpy())
    np.save("y_test.npy", y_test.to_numpy())

    return X_train_scaled, X_test_scaled, y_train, y_test

if __name__ == "__main__":
    try:
        # Test the preprocessing pipeline
        X_train, X_test, y_train, y_test = preprocess_data("training_data.csv")
        print("Data preprocessing completed successfully!")
        print(f"X_train shape: {X_train.shape}, X_test shape: {X_test.shape}")
        print(f"y_train shape: {y_train.shape}, y_test shape: {y_test.shape}")
    except Exception as e:
        print(f"Error during preprocessing: {e}")
