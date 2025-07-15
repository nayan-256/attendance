from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello World!"

@app.route('/test')
def test():
    return "Test route works!"

if __name__ == '__main__':
    print("Starting minimal Flask app...")
    app.run(debug=True, host='0.0.0.0', port=5001)
