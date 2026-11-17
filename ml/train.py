
import os
import pickle

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# 1. Memuat dataset Iris
iris = load_iris()

X = iris.data
y = iris.target

# 2. Membagi data training dan testing
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# 3. Membuat model Machine Learning
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

# 4. Melatih model
model.fit(X_train, y_train)

# 5. Menguji model
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("MODEL TRAINING BERHASIL!")
print("Accuracy:", accuracy)
print("\nClassification Report:")
print(classification_report(
    y_test,
    predictions,
    target_names=iris.target_names
))

# 6. Menyimpan model
os.makedirs("ml", exist_ok=True)

with open("ml/model.pkl", "wb") as file:
    pickle.dump(model, file)

print("\nModel berhasil disimpan di ml/model.pkl")
