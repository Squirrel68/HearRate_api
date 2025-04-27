from tensorflow import keras
import numpy as np

gpus = tf.config.experimental.list_physical_devices('GPU')
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)

# Limit memory growth for CPU
tf.config.threading.set_intra_op_parallelism_threads(1)
tf.config.threading.set_inter_op_parallelism_threads(1)

# Load model with optimizations
model = tf.keras.models.load_model('heart_disease_model.h5', compile=False)

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
