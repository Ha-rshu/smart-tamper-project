import os
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib

# Get project root
BASE_DIR = os.getcwd()
print("Base Directory:", BASE_DIR)

# Find training_data.csv automatically
csv_path = None

for root, dirs, files in os.walk(BASE_DIR):
    if "training_data.csv" in files:
        csv_path = os.path.join(root, "training_data.csv")
        break

if csv_path is None:
    print("❌ training_data.csv NOT FOUND anywhere!")
    exit()

print("✅ CSV Found At:", csv_path)

# Model path
model_path = os.path.join(BASE_DIR, "model", "risk_model.pkl")

# Load data
data = pd.read_csv(csv_path)

X = data[['size_diff', 'changed', 'frequency', 'time_gap']]
y = data['risk']

# Train model
model = DecisionTreeClassifier(max_depth=4)
model.fit(X, y)

# Save model
joblib.dump(model, model_path)

print("✅ AI Model Ready!")
