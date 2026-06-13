from flask import Flask, render_template, jsonify
import pymysql
from config import config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(config['default'])

def get_db_connection():
    config_obj = config['default']
    return pymysql.connect(
        host=config_obj.MYSQL_HOST,
        user=config_obj.MYSQL_USER,
        password=config_obj.MYSQL_PASSWORD,
        db=config_obj.MYSQL_DB,
        port=config_obj.MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def index():
    return render_template('index.html')

# 1. 总览指标API
@app.route('/api/overview')
def get_overview():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM overview_stats 
            ORDER BY date DESC LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        
        if result:
            data = {
                'total_electricity': float(result['total_electricity']),
                'classroom_usage_rate': float(result['classroom_usage_rate']),
                'avg_temperature': float(result['avg_temperature']),
                'avg_humidity': float(result['avg_humidity']),
                'online_devices': int(result['online_devices']),
                'alert_count': int(result['alert_count']),
                'date': result['date'].strftime('%Y-%m-%d')
            }
        else:
            data = {
                'total_electricity': 0,
                'classroom_usage_rate': 0,
                'avg_temperature': 0,
                'avg_humidity': 0,
                'online_devices': 0,
                'alert_count': 0,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 2. 教室使用率API（分时段）
@app.route('/api/classroom_usage')
def get_classroom_usage():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT time_slot, usage_rate, total_classrooms, used_classrooms
            FROM classroom_usage
            WHERE date = CURDATE()
            ORDER BY time_slot
        """)
        result = cursor.fetchall()
        conn.close()
        
        data = {
            'time_slots': [row['time_slot'] for row in result],
            'usage_rates': [float(row['usage_rate']) for row in result],
            'total_classrooms': [int(row['total_classrooms']) for row in result],
            'used_classrooms': [int(row['used_classrooms']) for row in result]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 3. 环境质量分析API
@app.route('/api/environment_quality')
def get_environment_quality():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT quality_level, count, percentage
            FROM environment_quality
            WHERE date = CURDATE()
            ORDER BY quality_level
        """)
        result = cursor.fetchall()
        conn.close()
        
        data = {
            'levels': [row['quality_level'] for row in result],
            'counts': [int(row['count']) for row in result],
            'percentages': [float(row['percentage']) for row in result]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 4. 楼栋活跃度排行API
@app.route('/api/building_activity')
def get_building_activity():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT building_name, activity_count
            FROM building_activity
            WHERE date = CURDATE()
            ORDER BY activity_count DESC
        """)
        result = cursor.fetchall()
        conn.close()
        
        data = {
            'buildings': [row['building_name'] for row in result],
            'activity_counts': [int(row['activity_count']) for row in result]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 5. 设备告警清单API
@app.route('/api/device_alerts')
def get_device_alerts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, device_name, device_type, status, alert_message, location, record_time
            FROM device_alert
            ORDER BY 
                CASE status 
                    WHEN '故障' THEN 1 
                    WHEN '预警' THEN 2 
                    WHEN '正常' THEN 3 
                END,
                record_time DESC
        """)
        result = cursor.fetchall()
        conn.close()
        
        data = {
            'alerts': [{
                'id': row['id'],
                'device_name': row['device_name'],
                'device_type': row['device_type'],
                'status': row['status'],
                'alert_message': row['alert_message'] or '-',
                'location': row['location'],
                'record_time': row['record_time'].strftime('%Y-%m-%d %H:%M')
            } for row in result]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 6. 设备状态统计API
@app.route('/api/device_stats')
def get_device_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM device_alert
            GROUP BY status
        """)
        result = cursor.fetchall()
        conn.close()
        
        stats = {'正常': 0, '预警': 0, '故障': 0}
        for row in result:
            stats[row['status']] = int(row['count'])
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)