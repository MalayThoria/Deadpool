"""
Health Analysis Data Seeder
Populates the database with comprehensive exercise and disease condition data
"""

from sqlalchemy.orm import Session
from database.config import get_db
from database.models import User  # Import User model
from database.health_analysis_models import (
    DiseaseCondition, HealthExercise, ExerciseCategory, DifficultyLevel,
    exercise_disease_association
)
import json

def seed_disease_conditions(db: Session):
    """Seed disease conditions with exercise considerations"""
    
    conditions_data = [
        {
            "name": "Type 2 Diabetes",
            "category": "endocrine",
            "description": "A chronic condition affecting blood sugar regulation",
            "severity_levels": ["mild", "moderate", "severe"],
            "exercise_restrictions": ["avoid_fasting_exercise", "monitor_blood_sugar"],
            "recommended_intensity": "moderate",
            "special_considerations": "Monitor blood glucose before, during, and after exercise. Carry glucose tablets.",
            "is_chronic": True,
            "requires_medical_clearance": True
        },
        {
            "name": "Hypertension",
            "category": "cardiovascular",
            "description": "High blood pressure condition",
            "severity_levels": ["stage_1", "stage_2", "crisis"],
            "exercise_restrictions": ["avoid_heavy_lifting", "avoid_isometric_exercises"],
            "recommended_intensity": "low_to_moderate",
            "special_considerations": "Avoid exercises that cause significant increases in blood pressure. Focus on aerobic activities.",
            "is_chronic": True,
            "requires_medical_clearance": True
        },
        {
            "name": "Arthritis",
            "category": "musculoskeletal",
            "description": "Joint inflammation and pain",
            "severity_levels": ["mild", "moderate", "severe"],
            "exercise_restrictions": ["avoid_high_impact", "joint_protection"],
            "recommended_intensity": "low_to_moderate",
            "special_considerations": "Focus on range of motion and low-impact activities. Exercise during times of least pain.",
            "is_chronic": True,
            "requires_medical_clearance": False
        },
        {
            "name": "Heart Disease",
            "category": "cardiovascular",
            "description": "Various conditions affecting heart function",
            "severity_levels": ["mild", "moderate", "severe"],
            "exercise_restrictions": ["cardiac_monitoring", "avoid_extreme_exertion"],
            "recommended_intensity": "low_to_moderate",
            "special_considerations": "Requires cardiac rehabilitation program. Monitor heart rate closely.",
            "is_chronic": True,
            "requires_medical_clearance": True
        },
        {
            "name": "Osteoporosis",
            "category": "musculoskeletal",
            "description": "Bone density loss increasing fracture risk",
            "severity_levels": ["osteopenia", "mild", "severe"],
            "exercise_restrictions": ["avoid_forward_flexion", "avoid_high_impact"],
            "recommended_intensity": "moderate",
            "special_considerations": "Focus on weight-bearing and resistance exercises. Avoid spinal flexion.",
            "is_chronic": True,
            "requires_medical_clearance": False
        },
        {
            "name": "COPD",
            "category": "respiratory",
            "description": "Chronic Obstructive Pulmonary Disease",
            "severity_levels": ["mild", "moderate", "severe", "very_severe"],
            "exercise_restrictions": ["oxygen_monitoring", "avoid_air_pollution"],
            "recommended_intensity": "low_to_moderate",
            "special_considerations": "Focus on breathing exercises and gradual endurance building. Use pursed-lip breathing.",
            "is_chronic": True,
            "requires_medical_clearance": True
        },
        {
            "name": "Lower Back Pain",
            "category": "musculoskeletal",
            "description": "Chronic or acute lower back pain",
            "severity_levels": ["mild", "moderate", "severe"],
            "exercise_restrictions": ["avoid_spinal_flexion", "core_strengthening_focus"],
            "recommended_intensity": "low_to_moderate",
            "special_considerations": "Focus on core strengthening and flexibility. Avoid exercises that worsen pain.",
            "is_chronic": False,
            "requires_medical_clearance": False
        },
        {
            "name": "Fibromyalgia",
            "category": "neurological",
            "description": "Chronic widespread musculoskeletal pain",
            "severity_levels": ["mild", "moderate", "severe"],
            "exercise_restrictions": ["gentle_progression", "fatigue_management"],
            "recommended_intensity": "low",
            "special_considerations": "Start very slowly and progress gradually. Focus on gentle movements and stress reduction.",
            "is_chronic": True,
            "requires_medical_clearance": False
        },
        {
            "name": "Obesity",
            "category": "metabolic",
            "description": "Excess body weight affecting health",
            "severity_levels": ["class_1", "class_2", "class_3"],
            "exercise_restrictions": ["joint_protection", "gradual_progression"],
            "recommended_intensity": "low_to_moderate",
            "special_considerations": "Focus on low-impact activities to protect joints. Emphasize consistency over intensity.",
            "is_chronic": True,
            "requires_medical_clearance": False
        },
        {
            "name": "Depression",
            "category": "mental_health",
            "description": "Mental health condition affecting mood and energy",
            "severity_levels": ["mild", "moderate", "severe"],
            "exercise_restrictions": ["motivation_support", "social_activities"],
            "recommended_intensity": "moderate",
            "special_considerations": "Exercise can significantly improve mood. Focus on enjoyable activities and social support.",
            "is_chronic": True,
            "requires_medical_clearance": False
        }
    ]
    
    for condition_data in conditions_data:
        existing = db.query(DiseaseCondition).filter(DiseaseCondition.name == condition_data["name"]).first()
        if not existing:
            condition = DiseaseCondition(**condition_data)
            db.add(condition)
    
    db.commit()

def seed_health_exercises(db: Session):
    """Seed comprehensive exercise database"""
    
    exercises_data = [
        {
            "name": "Walking",
            "category": ExerciseCategory.CARDIO,
            "difficulty_level": DifficultyLevel.BEGINNER,
            "description": "Low-impact cardiovascular exercise suitable for most conditions",
            "instructions": [
                "Start with comfortable pace",
                "Maintain upright posture",
                "Land on heel, roll to toe",
                "Swing arms naturally",
                "Breathe rhythmically"
            ],
            "duration_minutes": 30,
            "equipment_needed": ["comfortable_shoes"],
            "space_requirements": "outdoor_or_indoor",
            "primary_benefits": ["cardiovascular_health", "weight_management", "mood_improvement"],
            "muscle_groups_targeted": ["legs", "core", "cardiovascular_system"],
            "calories_per_minute": 4.0,
            "contraindications": ["severe_heart_failure", "unstable_angina"],
            "modifications": [
                "Use walking aids if needed",
                "Start with 5-10 minutes",
                "Walk on flat surfaces initially"
            ],
            "safety_tips": [
                "Wear proper footwear",
                "Stay hydrated",
                "Walk in safe areas",
                "Stop if experiencing chest pain"
            ],
            "medical_approval_required": False
        },
        {
            "name": "Chair Exercises",
            "category": ExerciseCategory.STRENGTH,
            "difficulty_level": DifficultyLevel.BEGINNER,
            "description": "Seated exercises for those with mobility limitations",
            "instructions": [
                "Sit upright in sturdy chair",
                "Keep feet flat on floor",
                "Engage core muscles",
                "Move slowly and controlled",
                "Breathe throughout movement"
            ],
            "duration_minutes": 20,
            "repetitions": 10,
            "sets": 2,
            "equipment_needed": ["sturdy_chair"],
            "space_requirements": "indoor",
            "primary_benefits": ["strength_maintenance", "circulation", "flexibility"],
            "muscle_groups_targeted": ["arms", "legs", "core"],
            "calories_per_minute": 2.5,
            "contraindications": ["severe_balance_issues"],
            "modifications": [
                "Use chair with arms for support",
                "Reduce range of motion if needed",
                "Add resistance bands for progression"
            ],
            "safety_tips": [
                "Ensure chair is stable",
                "Keep movements controlled",
                "Stop if dizzy"
            ],
            "medical_approval_required": False
        },
        {
            "name": "Water Aerobics",
            "category": ExerciseCategory.LOW_IMPACT,
            "difficulty_level": DifficultyLevel.EASY,
            "description": "Joint-friendly exercise in water",
            "instructions": [
                "Enter water gradually",
                "Start with gentle movements",
                "Use water resistance",
                "Maintain good posture",
                "Focus on full range of motion"
            ],
            "duration_minutes": 45,
            "equipment_needed": ["pool_access", "swimwear"],
            "space_requirements": "pool",
            "primary_benefits": ["joint_health", "cardiovascular_fitness", "muscle_strength"],
            "muscle_groups_targeted": ["full_body"],
            "calories_per_minute": 6.0,
            "contraindications": ["open_wounds", "severe_heart_conditions"],
            "modifications": [
                "Use pool noodles for support",
                "Stay in shallow end",
                "Reduce intensity as needed"
            ],
            "safety_tips": [
                "Never exercise alone in water",
                "Check water temperature",
                "Enter and exit pool carefully"
            ],
            "medical_approval_required": False
        },
        {
            "name": "Gentle Yoga",
            "category": ExerciseCategory.YOGA,
            "difficulty_level": DifficultyLevel.BEGINNER,
            "description": "Modified yoga poses for health conditions",
            "instructions": [
                "Start with breathing exercises",
                "Move slowly between poses",
                "Hold poses for 30 seconds",
                "Focus on alignment",
                "End with relaxation"
            ],
            "duration_minutes": 30,
            "equipment_needed": ["yoga_mat", "blocks", "straps"],
            "space_requirements": "indoor",
            "primary_benefits": ["flexibility", "stress_reduction", "balance"],
            "muscle_groups_targeted": ["full_body", "core"],
            "calories_per_minute": 3.0,
            "contraindications": ["severe_osteoporosis", "recent_surgery"],
            "modifications": [
                "Use chair for support",
                "Avoid deep twists",
                "Skip inversions if needed"
            ],
            "safety_tips": [
                "Don't force poses",
                "Listen to your body",
                "Use props for support"
            ],
            "medical_approval_required": False
        },
        {
            "name": "Resistance Band Training",
            "category": ExerciseCategory.STRENGTH,
            "difficulty_level": DifficultyLevel.EASY,
            "description": "Low-impact strength training with bands",
            "instructions": [
                "Choose appropriate resistance",
                "Maintain good posture",
                "Control both directions",
                "Keep tension throughout",
                "Breathe with movement"
            ],
            "duration_minutes": 25,
            "repetitions": 12,
            "sets": 2,
            "equipment_needed": ["resistance_bands"],
            "space_requirements": "indoor",
            "primary_benefits": ["muscle_strength", "bone_density", "functional_fitness"],
            "muscle_groups_targeted": ["arms", "legs", "core", "back"],
            "calories_per_minute": 4.5,
            "contraindications": ["acute_muscle_strain"],
            "modifications": [
                "Use lighter resistance",
                "Reduce range of motion",
                "Perform seated if needed"
            ],
            "safety_tips": [
                "Check bands for wear",
                "Secure anchor points",
                "Start with light resistance"
            ],
            "medical_approval_required": False
        },
        {
            "name": "Breathing Exercises",
            "category": ExerciseCategory.BREATHING,
            "difficulty_level": DifficultyLevel.BEGINNER,
            "description": "Focused breathing techniques for health",
            "instructions": [
                "Sit or lie comfortably",
                "Place one hand on chest, one on belly",
                "Breathe slowly through nose",
                "Feel belly rise more than chest",
                "Exhale slowly through mouth"
            ],
            "duration_minutes": 10,
            "equipment_needed": [],
            "space_requirements": "anywhere",
            "primary_benefits": ["stress_reduction", "lung_function", "relaxation"],
            "muscle_groups_targeted": ["diaphragm", "respiratory_muscles"],
            "calories_per_minute": 1.0,
            "contraindications": [],
            "modifications": [
                "Use different positions",
                "Vary breathing patterns",
                "Add visualization"
            ],
            "safety_tips": [
                "Don't force breathing",
                "Stop if dizzy",
                "Practice regularly"
            ],
            "medical_approval_required": False
        },
        {
            "name": "Balance Training",
            "category": ExerciseCategory.BALANCE,
            "difficulty_level": DifficultyLevel.EASY,
            "description": "Exercises to improve stability and prevent falls",
            "instructions": [
                "Start near wall or chair",
                "Focus on one point ahead",
                "Engage core muscles",
                "Start with both feet",
                "Progress to single leg"
            ],
            "duration_minutes": 15,
            "equipment_needed": ["sturdy_chair"],
            "space_requirements": "indoor",
            "primary_benefits": ["fall_prevention", "stability", "confidence"],
            "muscle_groups_targeted": ["core", "legs", "ankles"],
            "calories_per_minute": 2.0,
            "contraindications": ["severe_vertigo", "recent_falls"],
            "modifications": [
                "Hold onto support",
                "Reduce challenge level",
                "Practice on stable surface"
            ],
            "safety_tips": [
                "Have support nearby",
                "Practice on non-slip surface",
                "Progress gradually"
            ],
            "medical_approval_required": False
        },
        {
            "name": "Tai Chi",
            "category": ExerciseCategory.BALANCE,
            "difficulty_level": DifficultyLevel.EASY,
            "description": "Gentle martial art focusing on slow, flowing movements",
            "instructions": [
                "Stand with feet shoulder-width apart",
                "Keep movements slow and controlled",
                "Focus on weight shifting",
                "Coordinate with breathing",
                "Maintain relaxed posture"
            ],
            "duration_minutes": 30,
            "equipment_needed": [],
            "space_requirements": "indoor_or_outdoor",
            "primary_benefits": ["balance", "flexibility", "mental_focus"],
            "muscle_groups_targeted": ["full_body", "core"],
            "calories_per_minute": 3.5,
            "contraindications": ["severe_balance_disorders"],
            "modifications": [
                "Practice seated",
                "Use shorter sequences",
                "Hold onto chair for support"
            ],
            "safety_tips": [
                "Learn from qualified instructor",
                "Practice on level surface",
                "Wear appropriate footwear"
            ],
            "medical_approval_required": False
        }
    ]
    
    for exercise_data in exercises_data:
        existing = db.query(HealthExercise).filter(HealthExercise.name == exercise_data["name"]).first()
        if not existing:
            exercise = HealthExercise(**exercise_data)
            db.add(exercise)
    
    db.commit()

def seed_exercise_disease_mappings(db: Session):
    """Create mappings between exercises and disease conditions"""
    
    # Define mappings with effectiveness and safety scores
    mappings = [
        # Walking mappings
        ("Walking", "Type 2 Diabetes", 0.9, 0.95),
        ("Walking", "Hypertension", 0.85, 0.9),
        ("Walking", "Heart Disease", 0.8, 0.85),
        ("Walking", "Obesity", 0.9, 0.95),
        ("Walking", "Depression", 0.85, 0.95),
        ("Walking", "Arthritis", 0.7, 0.9),
        
        # Chair Exercises mappings
        ("Chair Exercises", "Arthritis", 0.8, 0.95),
        ("Chair Exercises", "COPD", 0.75, 0.9),
        ("Chair Exercises", "Heart Disease", 0.7, 0.9),
        ("Chair Exercises", "Fibromyalgia", 0.75, 0.95),
        ("Chair Exercises", "Osteoporosis", 0.8, 0.9),
        
        # Water Aerobics mappings
        ("Water Aerobics", "Arthritis", 0.95, 0.95),
        ("Water Aerobics", "Fibromyalgia", 0.85, 0.9),
        ("Water Aerobics", "Lower Back Pain", 0.8, 0.9),
        ("Water Aerobics", "Obesity", 0.85, 0.95),
        
        # Gentle Yoga mappings
        ("Gentle Yoga", "Lower Back Pain", 0.85, 0.9),
        ("Gentle Yoga", "Arthritis", 0.8, 0.85),
        ("Gentle Yoga", "Fibromyalgia", 0.8, 0.9),
        ("Gentle Yoga", "Depression", 0.85, 0.95),
        ("Gentle Yoga", "Hypertension", 0.75, 0.9),
        
        # Resistance Band Training mappings
        ("Resistance Band Training", "Osteoporosis", 0.9, 0.85),
        ("Resistance Band Training", "Type 2 Diabetes", 0.8, 0.9),
        ("Resistance Band Training", "Arthritis", 0.75, 0.85),
        ("Resistance Band Training", "COPD", 0.7, 0.85),
        
        # Breathing Exercises mappings
        ("Breathing Exercises", "COPD", 0.95, 0.95),
        ("Breathing Exercises", "Depression", 0.8, 0.95),
        ("Breathing Exercises", "Hypertension", 0.75, 0.95),
        ("Breathing Exercises", "Fibromyalgia", 0.7, 0.95),
        
        # Balance Training mappings
        ("Balance Training", "Osteoporosis", 0.85, 0.8),
        ("Balance Training", "Arthritis", 0.8, 0.85),
        ("Balance Training", "Fibromyalgia", 0.75, 0.9),
        
        # Tai Chi mappings
        ("Tai Chi", "Arthritis", 0.85, 0.9),
        ("Tai Chi", "Osteoporosis", 0.8, 0.85),
        ("Tai Chi", "Hypertension", 0.8, 0.9),
        ("Tai Chi", "Depression", 0.8, 0.95),
        ("Tai Chi", "Fibromyalgia", 0.8, 0.9),
    ]
    
    for exercise_name, condition_name, effectiveness, safety in mappings:
        exercise = db.query(HealthExercise).filter(HealthExercise.name == exercise_name).first()
        condition = db.query(DiseaseCondition).filter(DiseaseCondition.name == condition_name).first()
        
        if exercise and condition:
            # Check if mapping already exists
            existing = db.execute(
                exercise_disease_association.select().where(
                    (exercise_disease_association.c.exercise_id == exercise.id) &
                    (exercise_disease_association.c.disease_condition_id == condition.id)
                )
            ).first()
            
            if not existing:
                db.execute(
                    exercise_disease_association.insert().values(
                        exercise_id=exercise.id,
                        disease_condition_id=condition.id,
                        effectiveness_score=effectiveness,
                        safety_score=safety
                    )
                )
    
    db.commit()

def seed_all_health_data():
    """Seed all health analysis data"""
    from database.config import SessionLocal
    db = SessionLocal()
    
    try:
        print("Seeding disease conditions...")
        seed_disease_conditions(db)
        
        print("Seeding health exercises...")
        seed_health_exercises(db)
        
        print("Seeding exercise-disease mappings...")
        seed_exercise_disease_mappings(db)
        
        print("Health analysis data seeding completed successfully!")
        
    except Exception as e:
        print(f"Error seeding health data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_all_health_data()