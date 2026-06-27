import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import random

def generate_sample_xml(filename="export.xml", year=2026, month=2):
    root = ET.Element("HealthData")
    
    # We want to generate data for February 2026
    # Let's say we have 28 days in Feb 2026
    # We will generate daily values for the 5 metrics
    # sleep_duration (target 7h), steps (target 8000), active_energy (target 500 kcal),
    # exercise_time (target 30 min), stand_hours (target 12h)
    
    random.seed(42)  # For deterministic data
    
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, last_day)
    
    current_date = start_date
    while current_date <= end_date:
        # Occasionally miss a day (e.g., day 5, 12, 20) to test missing data behavior
        day = current_date.day
        if day in [5, 12, 20]:
            current_date += timedelta(days=1)
            continue
            
        # Steps
        steps_val = random.randint(4000, 12000)
        steps_start = current_date.replace(hour=10, minute=0, second=0)
        steps_end = steps_start + timedelta(minutes=5)
        ET.SubElement(root, "Record", {
            "type": "HKQuantityTypeIdentifierStepCount",
            "value": str(steps_val),
            "unit": "count",
            "startDate": steps_start.strftime("%Y-%m-%d %H:%M:%S +0900"),
            "endDate": steps_end.strftime("%Y-%m-%d %H:%M:%S +0900")
        })
        
        # Active Energy
        energy_val = random.randint(300, 750)
        energy_start = current_date.replace(hour=12, minute=0, second=0)
        energy_end = energy_start + timedelta(minutes=10)
        ET.SubElement(root, "Record", {
            "type": "HKQuantityTypeIdentifierActiveEnergyBurned",
            "value": str(energy_val),
            "unit": "kcal",
            "startDate": energy_start.strftime("%Y-%m-%d %H:%M:%S +0900"),
            "endDate": energy_end.strftime("%Y-%m-%d %H:%M:%S +0900")
        })
        
        # Exercise Time
        exercise_val = random.randint(15, 60)
        exercise_start = current_date.replace(hour=18, minute=0, second=0)
        exercise_end = exercise_start + timedelta(minutes=exercise_val)
        ET.SubElement(root, "Record", {
            "type": "HKQuantityTypeIdentifierAppleExerciseTime",
            "value": str(exercise_val),
            "unit": "min",
            "startDate": exercise_start.strftime("%Y-%m-%d %H:%M:%S +0900"),
            "endDate": exercise_end.strftime("%Y-%m-%d %H:%M:%S +0900")
        })
        
        # Stand Hours (stood for some hours)
        # Stand hour values are category Stood, usually recorded hourly
        num_stood = random.randint(8, 15)
        for hour in range(8, 8 + num_stood):
            stand_start = current_date.replace(hour=hour, minute=0, second=0)
            stand_end = stand_start + timedelta(minutes=2)
            ET.SubElement(root, "Record", {
                "type": "HKCategoryTypeIdentifierAppleStandHour",
                "value": "HKCategoryValueAppleStandHourStood",
                "startDate": stand_start.strftime("%Y-%m-%d %H:%M:%S +0900"),
                "endDate": stand_end.strftime("%Y-%m-%d %H:%M:%S +0900")
            })
            
        # Sleep duration (starts previous night, ends this morning)
        sleep_hours = random.uniform(5.5, 9.0)
        sleep_start = (current_date - timedelta(days=1)).replace(hour=23, minute=0, second=0)
        sleep_end = sleep_start + timedelta(hours=sleep_hours)
        ET.SubElement(root, "Record", {
            "type": "HKCategoryTypeIdentifierSleepAnalysis",
            "value": "HKCategoryValueSleepAnalysisAsleepCore",
            "startDate": sleep_start.strftime("%Y-%m-%d %H:%M:%S +0900"),
            "endDate": sleep_end.strftime("%Y-%m-%d %H:%M:%S +0900")
        })
        
        current_date += timedelta(days=1)
        
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    print(f"Generated {filename} successfully.")

if __name__ == "__main__":
    generate_sample_xml(month=6)
