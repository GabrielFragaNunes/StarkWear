from flask import Flask
from routes.index import setup_routes
import os
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)
setup_routes(app)

JSON_PATH = r"C:\Users\Gabriel\Documents\Roupas\api-project"
print("Arquivos no diretório JSON:")
print(os.listdir(JSON_PATH))

if __name__ == "__main__":
    app.run(debug=True)