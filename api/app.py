from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "API V360 rodando com sucesso!"}), 200

if __name__ == '__main__':
    app.run(debug=True)