import tensorflow as tf  # Add this import
from tensorflow import keras
import numpy as np
import os  # Add this import

# Set environment variable to reduce TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Initialize model as None for lazy loading
model = None

def load_model():
    global model
    if model is None:
        # Configure memory usage
        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        
        # Load model only when needed
        model = tf.keras.models.load_model('heart_disease_model.h5', compile=False)
    return model

# Predict
def predict_warning(features):
    # Get model (lazy loading)
    global model
    if model is None:
        model = load_model()
        
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
    
    # Predict with smaller batch size to reduce memory usage
    prediction = model.predict(X, batch_size=1)
    
    # Return prediction
    if prediction.shape[1] == 1:
        return int(prediction[0][0] > 0.5)
    else:
        return int(np.argmax(prediction[0]))