from flask import Flask, render_template, jsonify
import sqlite3
from config import config

app = Flask(__name__)
app.config.from_object(config['default'])

def get_db_connection():
    config_obj = config['default']
    conn = sqlite3.connect(config_obj.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/daily_consumption')
def get_daily_consumption():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, SUM(consumption_kwh) as total_consumption
            FROM energy_consumption
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        """)
        result = cursor.fetchall()
        conn.close()
        
        data = {
            'dates': [row['date'] for row in result][::-1],
            'consumption': [float(row['total_consumption']) for row in result][::-1]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/building_consumption')
def get_building_consumption():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT building, SUM(consumption_kwh) as total_consumption
            FROM energy_consumption
            GROUP BY building
            ORDER BY total_consumption DESC
        """)
        result = cursor.fetchall()
        conn.close()
        
        data = {
            'buildings': [row['building'] for row in result],
            'consumption': [float(row['total_consumption']) for row in result]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/solar_generation')
def get_solar_generation():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, SUM(generation_kwh) as total_generation
            FROM solar_generation
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        """)
        result = cursor.fetchall()
        conn.close()
        
        data = {
            'dates': [row['date'] for row in result][::-1],
            'generation': [float(row['total_generation']) for row in result][::-1]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather_trend')
def get_weather_trend():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, AVG(temperature) as avg_temp, AVG(humidity) as avg_humidity
            FROM weather_data
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        """)
        result = cursor.fetchall()
        conn.close()
        
        data = {
            'dates': [row['date'] for row in result][::-1],
            'temperature': [float(row['avg_temp']) for row in result][::-1],
            'humidity': [float(row['avg_humidity']) for row in result][::-1]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/energy_cost')
def get_energy_cost():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, total_cost, unit_price
            FROM energy_cost
            ORDER BY date DESC
            LIMIT 30
        """)
        result = cursor.fetchall()
        conn.close()
        
        data = {
            'dates': [row['date'] for row in result][::-1],
            'total_cost': [float(row['total_cost']) for row in result][::-1],
            'unit_price': [float(row['unit_price']) for row in result][::-1]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hourly_consumption')
def get_hourly_consumption():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT time, AVG(consumption_kwh) as avg_consumption
            FROM energy_consumption
            GROUP BY time
            ORDER BY time
        """)
        result = cursor.fetchall()
        conn.close()
        
        data = {
            'hours': [row['time'] for row in result],
            'consumption': [float(row['avg_consumption']) for row in result]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/summary')
def get_summary():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT SUM(consumption_kwh) as total FROM energy_consumption")
        total_consumption = float(cursor.fetchone()['total'] or 0)
        
        cursor.execute("SELECT SUM(generation_kwh) as total FROM solar_generation")
        total_generation = float(cursor.fetchone()['total'] or 0)
        
        cursor.execute("SELECT SUM(total_cost) as total FROM energy_cost")
        total_cost = float(cursor.fetchone()['total'] or 0)
        
        cursor.execute("SELECT AVG(efficiency) as avg FROM solar_generation WHERE efficiency IS NOT NULL")
        avg_efficiency = float(cursor.fetchone()['avg'] or 0)
        
        conn.close()
        
        data = {
            'total_consumption': round(total_consumption, 2),
            'total_generation': round(total_generation, 2),
            'total_cost': round(total_cost, 2),
            'avg_efficiency': round(avg_efficiency, 2)
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)