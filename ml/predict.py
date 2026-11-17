
import pickle
from pathlib import Path
from sklearn.datasets import load_iris

# Lokasi file model
MODEL_PATH = Path(__file__).parent / "model.pkl"

# Memuat model yang sudah dilatih
with open(MODEL_PATH, "rb") as file:
    model = pickle.load(file)

# Memuat nama kelas bunga
iris = load_iris()
flower_names = iris.target_names


def predict_flower(
    sepal_length: float,
    sepal_width: float,
    petal_length: float,
    petal_width: float
):
    # Menyiapkan input prediksi
    input_data = [[
        sepal_length,
        sepal_width,
        petal_length,
        petal_width
    ]]

    # Melakukan prediksi
    prediction = model.predict(input_data)[0]

    # Mengambil probabilitas prediksi
    probabilities = model.predict_proba(input_data)[0]

    return {
        "prediction": flower_names[prediction],
        "confidence": round(
            float(max(probabilities)) * 100, 2
        )
    }


if __name__ == "__main__":
    result = predict_flower(5.1, 3.5, 1.4, 0.2)

    print("HASIL PREDIKSI MACHINE LEARNING")
    print("Jenis bunga:", result["prediction"])
    print("Confidence:", result["confidence"], "%")
