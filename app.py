from flask import Flask, render_template, jsonify, send_from_directory, request
import pymysql
import os
from config import config
from datetime import datetime, timedelta

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

@app.route('/campus-model')
def serve_campus_model():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'campus.glb')

@app.route('/campus-model-2')
def serve_campus_model_2():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'campus2.0.glb')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename)

# 1. 分时段教室使用率
@app.route('/api/classroom_usage')
def get_classroom_usage():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT time_slot, usage_rate, total_rooms, used_rooms
            FROM campus_room_usage
            WHERE DATE(record_date) = CURDATE()
            ORDER BY time_slot
        """)
        result = cursor.fetchall()
        conn.close()
        
        time_slots = []
        usage_rates = []
        total_rooms = []
        used_rooms = []
        
        for row in result:
            time_slots.append(str(row['time_slot']))
            usage_rates.append(float(row['usage_rate']))
            total_rooms.append(int(row['total_rooms']))
            used_rooms.append(int(row['used_rooms']))
        
        avg_usage = sum(usage_rates) / len(usage_rates) if usage_rates else 0
        
        return jsonify({
            'time_slots': time_slots,
            'usage_rates': usage_rates,
            'total_rooms': total_rooms,
            'used_rooms': used_rooms,
            'avg_usage_rate': round(avg_usage, 1)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 2. 设备运行状态概览环形图
@app.route('/api/device_status_overview')
def get_device_status_overview():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取状态统计
        cursor.execute("""
            SELECT ds.status_name, COUNT(d.device_id) as count
            FROM campus_device d
            LEFT JOIN campus_device_status ds ON d.device_status = ds.status_id
            GROUP BY d.device_status, ds.status_name
        """)
        result = cursor.fetchall()
        
        status_map = {'正常': 0, '离线': 0, '故障': 0, '维修': 0}
        total = 0
        
        for row in result:
            status = row['status_name']
            count = int(row['count'])
            if status in status_map:
                status_map[status] = count
            total += count
        
        data = []
        for status, count in status_map.items():
            percentage = round(count / total * 100, 1) if total > 0 else 0
            data.append({
                'status': status,
                'count': count,
                'percentage': percentage
            })
        
        # 获取设备列表
        cursor.execute("""
            SELECT d.device_name, d.install_location as location, ds.status_name as status,
                   FLOOR(RAND() * 1000 + 100) as run_time
            FROM campus_device d
            LEFT JOIN campus_device_status ds ON d.device_status = ds.status_id
            ORDER BY d.device_id
        """)
        devices_result = cursor.fetchall()
        conn.close()
        
        devices = []
        for row in devices_result:
            devices.append({
                'device_name': row['device_name'],
                'location': row['location'],
                'status': row['status'],
                'run_time': f"{row['run_time']}小时"
            })
        
        return jsonify({
            'data': data,
            'total_devices': total,
            'online_devices': status_map['正常'],
            'devices': devices
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 3. 各楼栋活跃度排行柱状图
@app.route('/api/building_activity_rank')
def get_building_activity_rank():
    try:
        period = request.args.get('period', 'day')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if period == 'day':
            date_condition = "DATE(stat_date) = CURDATE()"
        elif period == 'week':
            date_condition = "stat_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif period == 'month':
            date_condition = "DATE_FORMAT(stat_date, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')"
        else:
            date_condition = "DATE(stat_date) = CURDATE()"
        
        cursor.execute(f"""
            SELECT b.building_name, AVG(ba.activity_score) as activity_score
            FROM campus_building_activity ba
            LEFT JOIN campus_building b ON ba.building_id = b.building_id
            WHERE {date_condition}
            GROUP BY ba.building_id, b.building_name
            ORDER BY activity_score DESC
        """)
        result = cursor.fetchall()
        conn.close()
        
        # 如果没有数据，返回示例数据
        if not result:
            buildings = ['教学楼A', '教学楼B', '宿舍楼A', '宿舍楼B', '图书馆', '体育馆', '实验楼', '食堂']
            activity_scores = [95.5, 88.2, 82.6, 78.3, 75.1, 68.9, 62.4, 55.8]
            return jsonify({
                'buildings': buildings,
                'activity_scores': activity_scores,
                'period': period
            })
        
        return jsonify({
            'buildings': [row['building_name'] for row in result],
            'activity_scores': [round(float(row['activity_score']), 1) for row in result],
            'period': period
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 4. 设备状态分类柱状图
@app.route('/api/device_type_stat')
def get_device_type_stat():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT dt.type_name,
                   SUM(CASE WHEN d.device_status = 1 THEN 1 ELSE 0 END) as normal_count,
                   SUM(CASE WHEN d.device_status = 3 THEN 1 ELSE 0 END) as fault_count,
                   SUM(CASE WHEN d.device_status = 2 THEN 1 ELSE 0 END) as offline_count
            FROM campus_device d
            LEFT JOIN campus_device_type dt ON d.type_id = dt.type_id
            GROUP BY d.type_id, dt.type_name
            ORDER BY dt.type_name
        """)
        result = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'type_names': [row['type_name'] for row in result],
            'normal_counts': [int(row['normal_count']) for row in result],
            'fault_counts': [int(row['fault_count']) for row in result],
            'offline_counts': [int(row['offline_count']) for row in result]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 5. 校园设备告警滚动清单
@app.route('/api/alarm_list')
def get_alarm_list():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as today_count
            FROM campus_device_alarm
            WHERE DATE(alarm_time) = CURDATE()
        """)
        today_count = cursor.fetchone()['today_count']
        
        cursor.execute("""
            SELECT da.alarm_id, d.device_name, b.building_name, 
                   da.alarm_level, da.alarm_message, da.alarm_time
            FROM campus_device_alarm da
            LEFT JOIN campus_device d ON da.device_id = d.device_id
            LEFT JOIN campus_building b ON d.building_id = b.building_id
            ORDER BY da.alarm_time DESC
            LIMIT 20
        """)
        result = cursor.fetchall()
        conn.close()
        
        alarms = []
        for row in result:
            alarms.append({
                'id': row['alarm_id'],
                'device_name': row['device_name'],
                'building_name': row['building_name'],
                'alarm_level': row['alarm_level'],
                'alarm_message': row['alarm_message'],
                'alarm_time': row['alarm_time'].strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'alarms': alarms,
            'today_count': int(today_count)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 6. 实时监测仪表盘
@app.route('/api/env_realtime_data')
def get_env_realtime_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.building_name, em.temperature, em.humidity, 
                   em.pm25, em.noise, em.monitor_time
            FROM (
                SELECT building_id, temperature, humidity, pm25, noise, monitor_time,
                       ROW_NUMBER() OVER (PARTITION BY building_id ORDER BY monitor_time DESC) as rn
                FROM campus_env_monitor
            ) em
            LEFT JOIN campus_building b ON em.building_id = b.building_id
            WHERE em.rn = 1
        """)
        result = cursor.fetchall()
        conn.close()
        
        devices = []
        temps = []
        humids = []
        
        for row in result:
            devices.append({
                'building_name': row['building_name'],
                'temperature': round(float(row['temperature']), 1),
                'humidity': round(float(row['humidity']), 1),
                'pm25': int(row['pm25']),
                'noise': round(float(row['noise']), 1),
                'monitor_time': row['monitor_time'].strftime('%Y-%m-%d %H:%M:%S')
            })
            temps.append(float(row['temperature']))
            humids.append(float(row['humidity']))
        
        avg_temp = round(sum(temps) / len(temps), 1) if temps else 0
        avg_humidity = round(sum(humids) / len(humids), 1) if humids else 0
        
        return jsonify({
            'devices': devices,
            'avg_temperature': avg_temp,
            'avg_humidity': avg_humidity
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 7. 校园环境质量雷达图
@app.route('/api/env_radar_analysis')
def get_env_radar_analysis():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ROUND(AVG(pm25), 1) as pm25,
                   ROUND(AVG(pm10), 1) as pm10,
                   ROUND(AVG(co2), 1) as co2,
                   ROUND(AVG(noise), 1) as noise,
                   ROUND(AVG(temperature), 1) as temperature,
                   ROUND(AVG(humidity), 1) as humidity
            FROM campus_env_monitor
            WHERE DATE(monitor_time) = CURDATE()
        """)
        result = cursor.fetchone()
        conn.close()
        
        # 处理None值，返回默认值
        def safe_float(value):
            return float(value) if value is not None else 0.0
        
        # 如果没有数据，返回示例数据
        if result['pm25'] is None:
            return jsonify({
                'dimensions': ['PM2.5', 'PM10', 'CO₂', '噪音', '温度', '湿度'],
                'values': [25.0, 45.0, 400.0, 55.0, 26.0, 60.0],
                'unit': ['μg/m³', 'μg/m³', 'ppm', 'dB', '°C', '%']
            })
        
        return jsonify({
            'dimensions': ['PM2.5', 'PM10', 'CO₂', '噪音', '温度', '湿度'],
            'values': [
                safe_float(result['pm25']),
                safe_float(result['pm10']),
                safe_float(result['co2']),
                safe_float(result['noise']),
                safe_float(result['temperature']),
                safe_float(result['humidity'])
            ],
            'unit': ['μg/m³', 'μg/m³', 'ppm', 'dB', '°C', '%']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 8. 能耗统计堆叠柱状图
@app.route('/api/energy_stat_data')
def get_energy_stat_data():
    try:
        period = request.args.get('period', 'day')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if period == 'day':
            # 获取最新的一天数据
            cursor.execute("""
                SELECT DATE(stat_date) as stat_day
                FROM campus_energy_stat
                WHERE building_id IS NOT NULL
                GROUP BY DATE(stat_date)
                ORDER BY DATE(stat_date) DESC
                LIMIT 1
            """)
            latest_day = cursor.fetchone()
            if latest_day:
                date_condition = f"DATE(stat_date) = '{latest_day['stat_day']}'"
            else:
                date_condition = "1=1"
            group_format = "%H:00"
        elif period == 'week':
            date_condition = "stat_date >= DATE_SUB((SELECT MAX(DATE(stat_date)) FROM campus_energy_stat), INTERVAL 6 DAY)"
            group_format = "%m-%d"
        elif period == 'month':
            date_condition = "DATE_FORMAT(stat_date, '%Y-%m') = DATE_FORMAT((SELECT MAX(stat_date) FROM campus_energy_stat), '%Y-%m')"
            group_format = "%m-%d"
        else:
            cursor.execute("""
                SELECT DATE(stat_date) as stat_day
                FROM campus_energy_stat
                WHERE building_id IS NOT NULL
                GROUP BY DATE(stat_date)
                ORDER BY DATE(stat_date) DESC
                LIMIT 1
            """)
            latest_day = cursor.fetchone()
            if latest_day:
                date_condition = f"DATE(stat_date) = '{latest_day['stat_day']}'"
            else:
                date_condition = "1=1"
            group_format = "%H:00"
        
        cursor.execute(f"""
            SELECT DATE_FORMAT(stat_date, '{group_format}') as time_label,
                   SUM(device_electric) as device_electric,
                   SUM(public_electric) as public_electric
            FROM campus_energy_stat
            WHERE {date_condition} AND building_id IS NOT NULL
            GROUP BY time_label
            ORDER BY MIN(stat_date)
        """)
        result = cursor.fetchall()
        
        cursor.execute(f"""
            SELECT electric_total
            FROM campus_energy_stat
            WHERE building_id IS NULL
            ORDER BY stat_date DESC
            LIMIT 1
        """)
        total_row = cursor.fetchone()
        conn.close()
        
        total_electric = float(total_row['electric_total']) if total_row else 0
        
        return jsonify({
            'time_labels': [row['time_label'] for row in result],
            'device_electric': [round(float(row['device_electric']), 1) for row in result],
            'public_electric': [round(float(row['public_electric']), 1) for row in result],
            'period': period,
            'total_electric': round(total_electric, 1)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
