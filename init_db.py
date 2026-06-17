import pymysql
from config import config
import random
from datetime import datetime, timedelta

def init_database():
    config_obj = config['default']
    
    try:
        connection = pymysql.connect(
            host=config_obj.MYSQL_HOST,
            user=config_obj.MYSQL_USER,
            password=config_obj.MYSQL_PASSWORD,
            port=config_obj.MYSQL_PORT
        )
        
        cursor = connection.cursor()
        
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config_obj.MYSQL_DB}")
        cursor.execute(f"USE {config_obj.MYSQL_DB}")
        
        # 创建新的数据表结构
        create_tables_sql = """
        -- 1. 教室使用表
        CREATE TABLE IF NOT EXISTS campus_room_usage (
            id INT AUTO_INCREMENT PRIMARY KEY,
            building_id INT,
            room_id VARCHAR(50),
            time_slot VARCHAR(10) NOT NULL,
            usage_rate DECIMAL(5, 2) NOT NULL,
            total_rooms INT NOT NULL,
            used_rooms INT NOT NULL,
            record_date DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 2. 设备表
        CREATE TABLE IF NOT EXISTS campus_device (
            device_id INT AUTO_INCREMENT PRIMARY KEY,
            device_name VARCHAR(100) NOT NULL,
            type_id INT,
            building_id INT,
            device_status INT DEFAULT 1 COMMENT '1正常, 2离线, 3故障, 4维修',
            install_location VARCHAR(200),
            last_maintain_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 3. 设备类型表
        CREATE TABLE IF NOT EXISTS campus_device_type (
            type_id INT AUTO_INCREMENT PRIMARY KEY,
            type_name VARCHAR(50) NOT NULL,
            type_desc VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 4. 设备状态表
        CREATE TABLE IF NOT EXISTS campus_device_status (
            status_id INT AUTO_INCREMENT PRIMARY KEY,
            status_name VARCHAR(20) NOT NULL,
            status_color VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 5. 楼栋表
        CREATE TABLE IF NOT EXISTS campus_building (
            building_id INT AUTO_INCREMENT PRIMARY KEY,
            building_name VARCHAR(100) NOT NULL,
            building_code VARCHAR(50),
            building_type VARCHAR(50),
            floor_count INT,
            area DECIMAL(10, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 6. 楼栋活跃度表
        CREATE TABLE IF NOT EXISTS campus_building_activity (
            id INT AUTO_INCREMENT PRIMARY KEY,
            building_id INT,
            activity_score DECIMAL(5, 2) NOT NULL,
            activity_count INT,
            stat_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 7. 设备告警表
        CREATE TABLE IF NOT EXISTS campus_device_alarm (
            alarm_id INT AUTO_INCREMENT PRIMARY KEY,
            device_id INT,
            alarm_level VARCHAR(20) NOT NULL COMMENT '正常/预警/故障',
            alarm_message VARCHAR(500),
            alarm_time DATETIME NOT NULL,
            is_handled INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 8. 环境监测表
        CREATE TABLE IF NOT EXISTS campus_env_monitor (
            id INT AUTO_INCREMENT PRIMARY KEY,
            building_id INT,
            temperature DECIMAL(5, 2),
            humidity DECIMAL(5, 2),
            pm25 DECIMAL(5, 2),
            pm10 DECIMAL(5, 2),
            co2 DECIMAL(8, 2),
            noise DECIMAL(5, 2),
            monitor_time DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 9. 能耗统计表
        CREATE TABLE IF NOT EXISTS campus_energy_stat (
            id INT AUTO_INCREMENT PRIMARY KEY,
            building_id INT,
            electric_total DECIMAL(12, 2),
            device_electric DECIMAL(12, 2),
            public_electric DECIMAL(12, 2),
            water_consume DECIMAL(12, 2),
            stat_date DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        for statement in create_tables_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        # 插入基础数据
        insert_base_data(cursor)
        
        # 插入模拟数据
        insert_sample_data(cursor)
        
        connection.commit()
        print("数据库初始化成功！")
        
    except Exception as e:
        print(f"数据库初始化错误: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

def insert_base_data(cursor):
    # 插入设备类型
    device_types = ['空调', '电梯', '监控', '饮水机', '照明', '门禁', '消防', '网络']
    for name in device_types:
        cursor.execute("INSERT IGNORE INTO campus_device_type (type_name) VALUES (%s)", (name,))
    
    # 插入设备状态
    cursor.execute("INSERT IGNORE INTO campus_device_status (status_id, status_name) VALUES (1, '正常')")
    cursor.execute("INSERT IGNORE INTO campus_device_status (status_id, status_name) VALUES (2, '离线')")
    cursor.execute("INSERT IGNORE INTO campus_device_status (status_id, status_name) VALUES (3, '故障')")
    cursor.execute("INSERT IGNORE INTO campus_device_status (status_id, status_name) VALUES (4, '维修')")
    
    # 插入楼栋数据
    buildings = [
        ('博文楼', 'BW', '教学建筑', 6, 12000),
        ('博远楼', 'BY', '教学建筑', 8, 15000),
        ('腾踏学生公寓', 'TT', '学生宿舍', 6, 8000),
        ('汇华学生公寓', 'HH', '学生宿舍', 6, 9000),
        ('弘毅学生公寓', 'HY', '学生宿舍', 5, 7500),
        ('景新学生公寓', 'JX', '学生宿舍', 6, 8500),
        ('景明学生公寓', 'JM', '学生宿舍', 6, 8200),
        ('博雅学生公寓', 'BYA', '学生宿舍', 5, 7800),
        ('明德楼', 'MD', '行政办公', 5, 6000),
        ('图书馆', 'TS', '图书信息', 4, 10000),
        ('学生活动中心', 'HD', '文体活动', 3, 5000),
        ('工程实训楼', 'GC', '实践教学', 4, 9000),
        ('任美福楼', 'RMF', '科研实验', 5, 7000),
        ('工学楼', 'GX', '教学建筑', 6, 11000),
        ('生科楼', 'SK', '科研实验', 5, 8500),
        ('体育馆', 'TY', '体育设施', 3, 12000),
        ('文鼎楼', 'WD', '教学建筑', 7, 10000)
    ]
    
    for name, code, type_name, floors, area in buildings:
        cursor.execute("""
            INSERT IGNORE INTO campus_building (building_name, building_code, building_type, floor_count, area)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, code, type_name, floors, area))

def insert_sample_data(cursor):
    today = datetime.now().date()
    
    # 1. 插入教室使用数据
    time_slots = ['08', '10', '12', '14', '16', '18', '20']
    for slot in time_slots:
        if slot in ['08', '10', '14']:
            usage_rate = round(random.uniform(70, 95), 2)
        elif slot == '12':
            usage_rate = round(random.uniform(20, 40), 2)
        elif slot in ['16', '18']:
            usage_rate = round(random.uniform(50, 70), 2)
        else:
            usage_rate = round(random.uniform(30, 50), 2)
        
        total_rooms = 120
        used_rooms = int(total_rooms * usage_rate / 100)
        cursor.execute("""
            INSERT INTO campus_room_usage (time_slot, usage_rate, total_rooms, used_rooms, record_date)
            VALUES (%s, %s, %s, %s, CURDATE())
        """, (slot, usage_rate, total_rooms, used_rooms))
    
    # 2. 插入设备数据
    device_names = [
        ('教学楼A空调1', 1, 1, 1), ('教学楼A空调2', 1, 1, 1), ('教学楼A空调3', 1, 1, 1),
        ('教学楼B空调1', 1, 2, 1), ('教学楼B空调2', 1, 2, 1), ('教学楼B空调3', 1, 2, 3),
        ('图书馆电梯1', 2, 10, 1), ('图书馆电梯2', 2, 10, 1),
        ('校门口监控', 3, 1, 1), ('食堂监控', 3, 17, 1), ('体育馆监控', 3, 16, 2),
        ('教学楼A饮水机', 4, 1, 1), ('宿舍楼饮水机', 4, 3, 4),
        ('行政楼门禁', 6, 9, 1), ('图书馆门禁', 6, 10, 1),
        ('实验楼消防', 7, 15, 1), ('体育馆消防', 7, 16, 1),
        ('网络设备1', 8, 1, 1), ('网络设备2', 8, 2, 1), ('网络设备3', 8, 10, 3)
    ]
    
    for name, type_id, building_id, status in device_names:
        cursor.execute("""
            INSERT INTO campus_device (device_name, type_id, building_id, device_status)
            VALUES (%s, %s, %s, %s)
        """, (name, type_id, building_id, status))
    
    # 3. 插入楼栋活跃度数据
    for building_id in range(1, 18):
        activity_score = round(random.uniform(0, 100), 2)
        activity_count = random.randint(100, 5000)
        cursor.execute("""
            INSERT INTO campus_building_activity (building_id, activity_score, activity_count, stat_date)
            VALUES (%s, %s, %s, CURDATE())
        """, (building_id, activity_score, activity_count))
    
    # 4. 插入设备告警数据
    for i in range(20):
        device_id = random.randint(1, 20)
        level = random.choice(['正常', '预警', '故障'])
        message = '设备运行正常' if level == '正常' else \
                  '设备状态异常，建议检查' if level == '预警' else '设备故障，请立即处理'
        alarm_time = datetime.now() - timedelta(minutes=random.randint(0, 120))
        cursor.execute("""
            INSERT INTO campus_device_alarm (device_id, alarm_level, alarm_message, alarm_time)
            VALUES (%s, %s, %s, %s)
        """, (device_id, level, message, alarm_time))
    
    # 5. 插入环境监测数据
    for building_id in range(1, 18):
        temp = round(random.uniform(18, 28), 1)
        humi = round(random.uniform(45, 75), 1)
        pm25 = random.randint(10, 40)
        pm10 = random.randint(20, 60)
        co2 = round(random.uniform(400, 1000), 1)
        noise = round(random.uniform(30, 60), 1)
        monitor_time = datetime.now() - timedelta(minutes=random.randint(0, 60))
        cursor.execute("""
            INSERT INTO campus_env_monitor (building_id, temperature, humidity, pm25, pm10, co2, noise, monitor_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (building_id, temp, humi, pm25, pm10, co2, noise, monitor_time))
    
    # 6. 插入能耗统计数据
    for hour in range(24):
        cursor.execute("""
            INSERT INTO campus_energy_stat (building_id, electric_total, device_electric, public_electric, stat_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (1, round(random.uniform(100, 500), 1), round(random.uniform(60, 300), 1), round(random.uniform(40, 200), 1), 
              datetime(today.year, today.month, today.day, hour, 0)))
    
    # 全校汇总数据
    cursor.execute("""
        INSERT INTO campus_energy_stat (building_id, electric_total, device_electric, public_electric, stat_date)
        VALUES (NULL, 15000, 9000, 6000, CURDATE())
    """)
    
    print("模拟数据插入成功！")

if __name__ == '__main__':
    init_database()
