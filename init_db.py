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
        
        # 创建5张数据表
        create_tables_sql = """
        -- 1. 总览指标表
        CREATE TABLE IF NOT EXISTS overview_stats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            total_electricity DECIMAL(10, 2) NOT NULL COMMENT '当日总用电量kWh',
            classroom_usage_rate DECIMAL(5, 2) NOT NULL COMMENT '教室综合使用率%',
            avg_temperature DECIMAL(5, 2) NOT NULL COMMENT '平均温度',
            avg_humidity DECIMAL(5, 2) NOT NULL COMMENT '平均湿度%',
            online_devices INT NOT NULL COMMENT '正常在线设备数',
            alert_count INT NOT NULL COMMENT '当日告警数量',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 2. 教室使用数据表
        CREATE TABLE IF NOT EXISTS classroom_usage (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            time_slot VARCHAR(20) NOT NULL COMMENT '时段如08:00-10:00',
            usage_rate DECIMAL(5, 2) NOT NULL COMMENT '使用率%',
            total_classrooms INT NOT NULL COMMENT '总教室数',
            used_classrooms INT NOT NULL COMMENT '已使用教室数',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 3. 环境质量数据表
        CREATE TABLE IF NOT EXISTS environment_quality (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            quality_level VARCHAR(10) NOT NULL COMMENT '优/良/差',
            count INT NOT NULL COMMENT '监测点数量',
            percentage DECIMAL(5, 2) NOT NULL COMMENT '占比%',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 4. 楼栋活跃度数据表
        CREATE TABLE IF NOT EXISTS building_activity (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            building_name VARCHAR(50) NOT NULL COMMENT '楼栋名称',
            activity_count INT NOT NULL COMMENT '活跃人次',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 5. 设备告警数据表
        CREATE TABLE IF NOT EXISTS device_alert (
            id INT AUTO_INCREMENT PRIMARY KEY,
            device_name VARCHAR(100) NOT NULL COMMENT '设备名称',
            device_type VARCHAR(50) NOT NULL COMMENT '设备类型',
            status VARCHAR(20) NOT NULL COMMENT '状态：正常/预警/故障',
            alert_message VARCHAR(200) COMMENT '异常说明',
            location VARCHAR(100) COMMENT '位置',
            record_time DATETIME NOT NULL COMMENT '记录时间',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        for statement in create_tables_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        # 插入模拟数据
        insert_sample_data(cursor)
        
        connection.commit()
        print("校园智慧运维数据库初始化成功！")
        
    except Exception as e:
        print(f"数据库初始化错误: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

def insert_sample_data(cursor):
    today = datetime.now().date()
    
    # 1. 插入总览指标数据（最近7天）
    for i in range(7):
        date = today - timedelta(days=i)
        total_electricity = round(random.uniform(8000, 15000), 2)
        classroom_usage_rate = round(random.uniform(60, 85), 2)
        avg_temperature = round(random.uniform(18, 28), 2)
        avg_humidity = round(random.uniform(45, 75), 2)
        online_devices = random.randint(180, 220)
        alert_count = random.randint(0, 15)
        
        cursor.execute("""
            INSERT INTO overview_stats (date, total_electricity, classroom_usage_rate, avg_temperature, avg_humidity, online_devices, alert_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (date, total_electricity, classroom_usage_rate, avg_temperature, avg_humidity, online_devices, alert_count))
    
    # 2. 插入教室使用数据（今日各时段）
    time_slots = ['08:00-10:00', '10:00-12:00', '12:00-14:00', '14:00-16:00', '16:00-18:00', '18:00-20:00', '20:00-22:00']
    total_classrooms = 120
    
    for slot in time_slots:
        # 模拟不同时段的使用率（上课时段高，午休时段低）
        if slot in ['08:00-10:00', '10:00-12:00', '14:00-16:00']:
            usage_rate = round(random.uniform(70, 95), 2)
        elif slot == '12:00-14:00':
            usage_rate = round(random.uniform(20, 40), 2)
        elif slot in ['16:00-18:00', '18:00-20:00']:
            usage_rate = round(random.uniform(50, 70), 2)
        else:
            usage_rate = round(random.uniform(30, 50), 2)
        
        used_classrooms = int(total_classrooms * usage_rate / 100)
        
        cursor.execute("""
            INSERT INTO classroom_usage (date, time_slot, usage_rate, total_classrooms, used_classrooms)
            VALUES (%s, %s, %s, %s, %s)
        """, (today, slot, usage_rate, total_classrooms, used_classrooms))
    
    # 3. 插入环境质量数据
    quality_data = [
        ('优', random.randint(15, 25), round(random.uniform(60, 75), 2)),
        ('良', random.randint(8, 15), round(random.uniform(20, 35), 2)),
        ('差', random.randint(1, 5), round(random.uniform(2, 10), 2))
    ]
    
    for level, count, percentage in quality_data:
        cursor.execute("""
            INSERT INTO environment_quality (date, quality_level, count, percentage)
            VALUES (%s, %s, %s, %s)
        """, (today, level, count, percentage))
    
    # 4. 插入楼栋活跃度数据
    buildings = ['教学楼A', '教学楼B', '实训楼', '图书馆', '宿舍楼1', '宿舍楼2', '食堂', '体育馆', '行政楼', '实验楼']
    
    for building in buildings:
        # 不同楼栋活跃度差异
        if building in ['教学楼A', '教学楼B', '实训楼']:
            activity_count = random.randint(2000, 5000)
        elif building in ['宿舍楼1', '宿舍楼2', '食堂']:
            activity_count = random.randint(1500, 3500)
        elif building == '图书馆':
            activity_count = random.randint(800, 2000)
        else:
            activity_count = random.randint(300, 1000)
        
        cursor.execute("""
            INSERT INTO building_activity (date, building_name, activity_count)
            VALUES (%s, %s, %s)
        """, (today, building, activity_count))
    
    # 5. 插入设备告警数据
    devices = [
        ('空调-教学楼A301', '空调', '正常', None, '教学楼A 3层'),
        ('空调-教学楼A302', '空调', '正常', None, '教学楼A 3层'),
        ('电梯-图书馆1号', '电梯', '正常', None, '图书馆主楼'),
        ('监控-校门口', '监控', '正常', None, '校门入口'),
        ('饮水机-教学楼B', '饮水机', '预警', '水温异常，需检修', '教学楼B 1层'),
        ('空调-实训楼201', '空调', '故障', '压缩机故障，已停机', '实训楼 2层'),
        ('电梯-宿舍楼1号', '电梯', '正常', None, '宿舍楼1'),
        ('监控-食堂入口', '监控', '正常', None, '食堂入口'),
        ('空调-图书馆阅览室', '空调', '预警', '制冷效果下降', '图书馆2层'),
        ('饮水机-体育馆', '饮水机', '正常', None, '体育馆大厅'),
        ('电梯-行政楼', '电梯', '故障', '门禁系统故障', '行政楼1层'),
        ('监控-教学楼A走廊', '监控', '正常', None, '教学楼A'),
        ('空调-实验楼101', '空调', '正常', None, '实验楼1层'),
        ('饮水机-宿舍楼2', '饮水机', '预警', '滤芯需更换', '宿舍楼2大厅'),
        ('监控-体育馆', '监控', '正常', None, '体育馆内部')
    ]
    
    for device_name, device_type, status, alert_message, location in devices:
        record_time = datetime.now() - timedelta(minutes=random.randint(0, 120))
        cursor.execute("""
            INSERT INTO device_alert (device_name, device_type, status, alert_message, location, record_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (device_name, device_type, status, alert_message, location, record_time))
    
    print("模拟数据插入成功！")

if __name__ == '__main__':
    init_database()