from flask import Blueprint

routes = Blueprint('routes', __name__)

@routes.route('/', methods=['GET'])
def index():
    return 'index.html'