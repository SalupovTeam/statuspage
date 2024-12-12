from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import requests
import threading
import time
import os
import markdown2

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///statuspage.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
LOGO_IMG = os.getenv('LOGO_IMG', '')

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WebInfo(db.Model):
    __tablename__ = 'web_info'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(500))

class Component(db.Model):
    __tablename__ = 'components'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    website = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StatusUpdate(db.Model):
    __tablename__ = 'status_updates'
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'))
    status = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def verify_api_key():
    api_key = request.headers.get('x-api-key')
    if not api_key:
        return False
    return bool(ApiKey.query.filter_by(key=api_key).first())

@app.route('/add', methods=['POST'])
def add_component():
    if not verify_api_key():
        return jsonify({'error': 'Invalid API key'}), 401

    data = request.json
    name = data.get('name')
    website = data.get('website')

    if not name or not website:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        component = Component(name=name, website=website)
        db.session.add(component)
        db.session.commit()
        return jsonify({'message': 'Component added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    
@app.route('/docs')
def api_docs():
    with open('api_docs.md', 'r') as f:
        content = f.read()
    
    html = markdown2.markdown(content, extras=["fenced-code-blocks", "tables"])
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }}
            pre {{
                background: #f6f8fa;
                padding: 16px;
                border-radius: 6px;
                overflow-x: auto;
            }}
            code {{
                background: #f6f8fa;
                padding: 2px 4px;
                border-radius: 4px;
            }}
            h1, h2, h3 {{
                border-bottom: 2px solid #eaecef;
                padding-bottom: 0.3em;
            }}
            .json {{
                color: #032f62;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }}
            th, td {{
                border: 1px solid #dfe2e5;
                padding: 6px 13px;
            }}
            th {{
                background: #f6f8fa;
            }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """

@app.route('/update', methods=['POST'])
def update_status():
    if not verify_api_key():
        return jsonify({'error': 'Invalid API key'}), 401

    data = request.json
    name = data.get('name')
    status = data.get('status')
    date_str = data.get('date')

    if not all([name, status, date_str]):
        return jsonify({'error': 'Missing required fields'}), 400

    if status not in ['working', 'outage']:
        return jsonify({'error': 'Invalid status'}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        component = Component.query.filter_by(name=name).first()
        if not component:
            return jsonify({'error': 'Component not found'}), 404

        status_update = StatusUpdate(
            component_id=component.id,
            status=status,
            date=date
        )
        db.session.add(status_update)
        db.session.commit()
        return jsonify({'message': 'Status updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/list')
def list_components():
    components = Component.query.all()
    result = []

    for component in components:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)

        status_updates = StatusUpdate.query.filter(
            StatusUpdate.component_id == component.id,
            StatusUpdate.date >= start_date,
            StatusUpdate.date <= end_date
        ).order_by(StatusUpdate.date).all()

        daily_status = {}
        for update in status_updates:
            date_key = update.date.strftime('%Y-%m-%d')
            if date_key not in daily_status:
                daily_status[date_key] = set()
            daily_status[date_key].add(update.status)

        status_colors = []
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            statuses = daily_status.get(date_key, set())

            if not statuses:
                color = 'gray'
            elif statuses == {'working'}:
                color = 'green'
            elif statuses == {'outage'}:
                color = 'red'
            else:
                color = 'orange'

            status_colors.append(color)
            current_date += timedelta(days=1)

        result.append({
            'name': component.name,
            'website': component.website,
            'status_history': status_colors
        })

    return jsonify(result)

@app.route('/')
def index():
     return render_template('index.html')

@app.route('/logo')
def serve_logo():
    return send_from_directory('templates', 'logo.png')

@app.route('/favicon')
def serve_favicon():
    return send_from_directory('templates', 'favicon.png')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1487)
