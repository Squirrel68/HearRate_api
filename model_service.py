from tensorflow import keras
import numpy as np

# Load model
model = keras.models.load_model('heart_disease_model.h5')

# Predict
def predict_warning(features):

    bpm = features.get('bpm', 0)
    X = np.array([[
        features['age'],
        features['gender'],
        features['height'],
        features['weight'],
        bpm,
        bpm,
        features['smoke'],
        features['alco'],
    ]])
    
    # Nếu bạn cần chuẩn hóa, phải load scaler thêm
    # ví dụ: X_scaled = scaler.transform(X)
    # (Bạn cần lưu `scaler` nữa)
    
    prediction = model.predict(X)
    
    # Nếu binary, sẽ ra giá trị (0-1), cần round
    if prediction.shape[1] == 1:
        return int(prediction[0][0] > 0.5)
    else:
        return int(np.argmax(prediction[0]))
