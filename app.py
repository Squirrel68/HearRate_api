from flask import Flask, request, jsonify
from firebase_service import get_user_heart_data
from model_service import predict_warning

app = Flask(__name__)

@app.route('/realtime-heart', methods=['GET'])
def get_realtime_heart():
    user_id = request.args.get('userId')

    # Lấy dữ liệu nhịp tim mới nhất từ Firebase
    data = get_user_heart_data(user_id)
    if not data:
        return jsonify({'error': 'User data not found'}), 404

    bpm = data.get('bpm')
    spo2 = data.get('spo2')

    # Giả sử bạn cũng lưu thông tin profile user ở đâu đó (hoặc mock tạm)
    user_profile = {
        'age': 25,
        'gender': 1,
        'height': 170,
        'weight': 65,
        'ap_hi': 120,
        'ap_lo': 80,
        'smoke': 0,
        'alco': 0
    }

    user_profile['bpm'] = bpm
    user_profile['spo2'] = spo2

    # Dự đoán
    warning = predict_warning(user_profile)

    response = {
        'userId': user_id,
        'bpm': bpm,
        'spo2': spo2,
        'warning': warning  # 1 = bất thường, 0 = bình thường
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
