from flask import Blueprint
from controllers.index import get_all_jsons, get_json_by_name

def setup_routes(app):
    api_bp = Blueprint('api', __name__)
    api_bp.route('/json/todos-jsons', methods=['GET'])(get_all_jsons)
    api_bp.route('/json/<nome>', methods=['GET'])(get_json_by_name)
    app.register_blueprint(api_bp)