from flask import Blueprint, render_template, redirect, url_for

route = Blueprint('route', __name__, url_prefix='/')

@route.route('/')
def index():
    return redirect(url_for('route.version5'))

@route.route('/classe', methods=['GET'])
def version5():
    return render_template('pages/lidar_classe.html')