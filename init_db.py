import pymysql
from config import config

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
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config_obj.MYSQL_DB}")
        cursor.execute(f"USE {config_obj.MYSQL_DB}")
        
        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS energy_consumption (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            time TIME NOT NULL,
            building VARCHAR(50) NOT NULL,
            consumption_kwh DECIMAL(10, 2) NOT NULL,
            peak_power_kw DECIMAL(10, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS solar_generation (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            time TIME NOT NULL,
            generation_kwh DECIMAL(10, 2) NOT NULL,
            efficiency DECIMAL(5, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS weather_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            time TIME NOT NULL,
            temperature DECIMAL(5, 2),
            humidity DECIMAL(5, 2),
            wind_speed DECIMAL(5, 2),
            solar_radiation DECIMAL(8, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS energy_cost (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            total_cost DECIMAL(10, 2) NOT NULL,
            unit_price DECIMAL(6, 4) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        for statement in create_tables_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        insert_sample_data(cursor)
        
        connection.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

def insert_sample_data(cursor):
    import random
    from datetime import datetime, timedelta
    
    buildings = ['Main Office', 'Warehouse A', 'Warehouse B', 'Parking Garage', 'Workshop']
    
    base_date = datetime(2024, 1, 1)
    for i in range(30):
        current_date = base_date + timedelta(days=i)
        for hour in range(24):
            current_time = f"{hour:02d}:00:00"
            
            for building in buildings:
                consumption = round(random.uniform(10, 100), 2)
                peak_power = round(random.uniform(5, 50), 2)
                cursor.execute("""
                    INSERT INTO energy_consumption (date, time, building, consumption_kwh, peak_power_kw)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE consumption_kwh = VALUES(consumption_kwh)
                """, (current_date.date(), current_time, building, consumption, peak_power))
            
            solar_gen = round(random.uniform(0, 80), 2) if 6 <= hour <= 18 else 0
            efficiency = round(random.uniform(15, 22), 2) if solar_gen > 0 else None
            cursor.execute("""
                INSERT INTO solar_generation (date, time, generation_kwh, efficiency)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE generation_kwh = VALUES(generation_kwh)
            """, (current_date.date(), current_time, solar_gen, efficiency))
            
            temp = round(random.uniform(-5, 35), 2)
            humidity = round(random.uniform(30, 90), 2)
            wind_speed = round(random.uniform(0, 20), 2)
            solar_rad = round(random.uniform(0, 1000), 2) if 6 <= hour <= 18 else 0
            cursor.execute("""
                INSERT INTO weather_data (date, time, temperature, humidity, wind_speed, solar_radiation)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE temperature = VALUES(temperature)
            """, (current_date.date(), current_time, temp, humidity, wind_speed, solar_rad))
        
        daily_cost = round(random.uniform(500, 2000), 2)
        unit_price = round(random.uniform(0.5, 0.8), 4)
        cursor.execute("""
            INSERT INTO energy_cost (date, total_cost, unit_price)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE total_cost = VALUES(total_cost)
        """, (current_date.date(), daily_cost, unit_price))
    
    print("Sample data inserted successfully!")

if __name__ == '__main__':
    init_database()