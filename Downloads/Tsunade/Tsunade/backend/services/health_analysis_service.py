"""
Health Analysis Service
Provides intelligent exercise recommendations based on user health conditions
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
import json
import logging

from database.health_analysis_models import (
    DiseaseCondition, HealthExercise, PersonalizedExerciseRecommendation,
    UserHealthAnalysisProfile, ExerciseSchedule, exercise_disease_association,
    RecommendationStatus, ScheduleFrequency, ExerciseCategory, DifficultyLevel
)
from database.models import User

logger = logging.getLogger(__name__)

class HealthAnalysisService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_disease_conditions(self) -> List[Dict]:
        """Get all available disease conditions for user selection"""
        conditions = self.db.query(DiseaseCondition).all()
        return [
            {
                "id": condition.id,
                "name": condition.name,
                "category": condition.category,
                "description": condition.description,
                "severity_levels": condition.severity_levels,
                "requires_medical_clearance": condition.requires_medical_clearance,
                "is_chronic": condition.is_chronic
            }
            for condition in conditions
        ]
    
    def search_disease_conditions(self, query: str) -> List[Dict]:
        """Search disease conditions by name or category"""
        conditions = self.db.query(DiseaseCondition).filter(
            or_(
                DiseaseCondition.name.ilike(f"%{query}%"),
                DiseaseCondition.category.ilike(f"%{query}%"),
                DiseaseCondition.description.ilike(f"%{query}%")
            )
        ).all()
        
        return [
            {
                "id": condition.id,
                "name": condition.name,
                "category": condition.category,
                "description": condition.description,
                "severity_levels": condition.severity_levels,
                "requires_medical_clearance": condition.requires_medical_clearance
            }
            for condition in conditions
        ]
    
    def create_user_health_profile(self, user_id: int, profile_data: Dict) -> Dict:
        """Create or update user health analysis profile"""
        existing_profile = self.db.query(UserHealthAnalysisProfile).filter(
            UserHealthAnalysisProfile.user_id == user_id
        ).first()
        
        if existing_profile:
            # Update existing profile
            for key, value in profile_data.items():
                if hasattr(existing_profile, key):
                    setattr(existing_profile, key, value)
            existing_profile.updated_at = datetime.utcnow()
            profile = existing_profile
        else:
            # Create new profile
            profile = UserHealthAnalysisProfile(
                user_id=user_id,
                **profile_data
            )
            self.db.add(profile)
        
        self.db.commit()
        self.db.refresh(profile)
        
        return {
            "id": profile.id,
            "user_id": profile.user_id,
            "current_conditions": profile.current_conditions,
            "fitness_level": profile.fitness_level,
            "exercise_preferences": profile.exercise_preferences,
            "primary_goals": profile.primary_goals,
            "available_time_per_session": profile.available_time_per_session,
            "equipment_available": profile.equipment_available
        }
    
    def generate_exercise_recommendations(self, user_id: int, condition_ids: List[int], 
                                        user_preferences: Optional[Dict] = None) -> List[Dict]:
        """Generate personalized exercise recommendations based on conditions"""
        
        # Get user profile if exists
        user_profile = self.db.query(UserHealthAnalysisProfile).filter(
            UserHealthAnalysisProfile.user_id == user_id
        ).first()
        
        # Get conditions
        conditions = self.db.query(DiseaseCondition).filter(
            DiseaseCondition.id.in_(condition_ids)
        ).all()
        
        if not conditions:
            return []
        
        # Find exercises suitable for all conditions
        suitable_exercises = self._find_suitable_exercises(conditions, user_preferences)
        
        # Generate personalized recommendations
        recommendations = []
        for exercise_data in suitable_exercises:
            exercise = exercise_data['exercise']
            avg_effectiveness = exercise_data['avg_effectiveness']
            avg_safety = exercise_data['avg_safety']
            
            # Create recommendation for each condition
            for condition in conditions:
                recommendation_data = self._create_recommendation_data(
                    user_id, exercise, condition, user_profile, 
                    avg_effectiveness, avg_safety
                )
                
                # Check if recommendation already exists
                existing = self.db.query(PersonalizedExerciseRecommendation).filter(
                    and_(
                        PersonalizedExerciseRecommendation.user_id == user_id,
                        PersonalizedExerciseRecommendation.exercise_id == exercise.id,
                        PersonalizedExerciseRecommendation.condition_id == condition.id,
                        PersonalizedExerciseRecommendation.status == RecommendationStatus.ACTIVE
                    )
                ).first()
                
                if not existing:
                    recommendation = PersonalizedExerciseRecommendation(**recommendation_data)
                    self.db.add(recommendation)
                    self.db.flush()
                    recommendations.append(self._format_recommendation(recommendation))
                else:
                    recommendations.append(self._format_recommendation(existing))
        
        self.db.commit()
        
        # Sort by priority score (highest first)
        recommendations.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _find_suitable_exercises(self, conditions: List[DiseaseCondition], 
                               user_preferences: Optional[Dict] = None) -> List[Dict]:
        """Find exercises suitable for given conditions"""
        
        # Get all exercises mapped to these conditions
        condition_ids = [c.id for c in conditions]
        
        query = self.db.query(
            HealthExercise,
            func.avg(exercise_disease_association.c.effectiveness_score).label('avg_effectiveness'),
            func.avg(exercise_disease_association.c.safety_score).label('avg_safety'),
            func.count(exercise_disease_association.c.disease_condition_id).label('condition_count')
        ).join(
            exercise_disease_association,
            HealthExercise.id == exercise_disease_association.c.exercise_id
        ).filter(
            and_(
                exercise_disease_association.c.disease_condition_id.in_(condition_ids),
                HealthExercise.is_active == True
            )
        ).group_by(HealthExercise.id)
        
        # Apply user preferences if provided
        if user_preferences:
            if 'fitness_level' in user_preferences:
                fitness_level = user_preferences['fitness_level']
                if fitness_level == 'beginner':
                    query = query.filter(HealthExercise.difficulty_level.in_([
                        DifficultyLevel.BEGINNER, DifficultyLevel.EASY
                    ]))
                elif fitness_level == 'intermediate':
                    query = query.filter(HealthExercise.difficulty_level.in_([
                        DifficultyLevel.EASY, DifficultyLevel.MODERATE
                    ]))
            
            if 'exercise_preferences' in user_preferences:
                preferred_categories = user_preferences['exercise_preferences']
                if preferred_categories:
                    category_enums = [ExerciseCategory(cat) for cat in preferred_categories 
                                    if cat in [e.value for e in ExerciseCategory]]
                    if category_enums:
                        query = query.filter(HealthExercise.category.in_(category_enums))
            
            if 'available_time_per_session' in user_preferences:
                max_time = user_preferences['available_time_per_session']
                if max_time:
                    query = query.filter(HealthExercise.duration_minutes <= max_time)
        
        results = query.all()
        
        # Filter exercises that are suitable for ALL conditions (high safety score)
        suitable_exercises = []
        for exercise, avg_effectiveness, avg_safety, condition_count in results:
            if avg_safety >= 0.7 and avg_effectiveness >= 0.6:  # Minimum thresholds
                suitable_exercises.append({
                    'exercise': exercise,
                    'avg_effectiveness': float(avg_effectiveness),
                    'avg_safety': float(avg_safety),
                    'condition_count': condition_count
                })
        
        # Sort by safety first, then effectiveness
        suitable_exercises.sort(key=lambda x: (x['avg_safety'], x['avg_effectiveness']), reverse=True)
        
        return suitable_exercises
    
    def _create_recommendation_data(self, user_id: int, exercise: HealthExercise, 
                                  condition: DiseaseCondition, user_profile: Optional[UserHealthAnalysisProfile],
                                  effectiveness: float, safety: float) -> Dict:
        """Create recommendation data with personalization"""
        
        # Base recommendation data
        recommendation_data = {
            'user_id': user_id,
            'exercise_id': exercise.id,
            'condition_id': condition.id,
            'status': RecommendationStatus.ACTIVE,
            'priority_score': self._calculate_priority_score(exercise, condition, effectiveness, safety)
        }
        
        # Personalize duration
        base_duration = exercise.duration_minutes or 30
        if user_profile and user_profile.available_time_per_session:
            max_time = user_profile.available_time_per_session
            recommendation_data['recommended_duration'] = min(base_duration, max_time)
        else:
            recommendation_data['recommended_duration'] = base_duration
        
        # Determine frequency based on condition and exercise type
        recommendation_data['recommended_frequency'] = self._determine_frequency(exercise, condition)
        
        # Set intensity based on condition severity and user fitness level
        recommendation_data['recommended_intensity'] = self._determine_intensity(
            condition, user_profile, exercise
        )
        
        # Generate AI reasoning
        recommendation_data['reasoning'] = self._generate_reasoning(exercise, condition, effectiveness, safety)
        
        # Set expected benefits
        recommendation_data['expected_benefits'] = self._determine_expected_benefits(exercise, condition)
        
        # Apply modifications if needed
        recommendation_data['modifications_applied'] = self._determine_modifications(
            exercise, condition, user_profile
        )
        
        # Set scheduling
        recommendation_data['start_date'] = datetime.utcnow()
        recommendation_data['target_end_date'] = datetime.utcnow() + timedelta(weeks=12)  # 3 months
        
        return recommendation_data
    
    def _calculate_priority_score(self, exercise: HealthExercise, condition: DiseaseCondition,
                                effectiveness: float, safety: float) -> float:
        """Calculate priority score for recommendation"""
        base_score = (effectiveness * 0.4 + safety * 0.6)  # Safety weighted higher
        
        # Boost score for certain conditions
        if condition.requires_medical_clearance:
            base_score *= 0.9  # Slightly lower priority for high-risk conditions
        
        if condition.is_chronic:
            base_score *= 1.1  # Higher priority for chronic conditions
        
        # Boost score for beginner-friendly exercises
        if exercise.difficulty_level in [DifficultyLevel.BEGINNER, DifficultyLevel.EASY]:
            base_score *= 1.05
        
        return min(base_score, 1.0)  # Cap at 1.0
    
    def _determine_frequency(self, exercise: HealthExercise, condition: DiseaseCondition) -> ScheduleFrequency:
        """Determine recommended frequency based on exercise and condition"""
        
        # High-impact or strength exercises
        if exercise.category in [ExerciseCategory.STRENGTH, ExerciseCategory.CARDIO]:
            if condition.recommended_intensity == "low":
                return ScheduleFrequency.THREE_TIMES_WEEK
            else:
                return ScheduleFrequency.EVERY_OTHER_DAY
        
        # Low-impact exercises can be done more frequently
        elif exercise.category in [ExerciseCategory.FLEXIBILITY, ExerciseCategory.BALANCE, 
                                 ExerciseCategory.BREATHING, ExerciseCategory.YOGA]:
            return ScheduleFrequency.DAILY
        
        # Default
        return ScheduleFrequency.THREE_TIMES_WEEK
    
    def _determine_intensity(self, condition: DiseaseCondition, 
                           user_profile: Optional[UserHealthAnalysisProfile],
                           exercise: HealthExercise) -> str:
        """Determine recommended intensity"""
        
        # Start with condition's recommended intensity
        condition_intensity = condition.recommended_intensity or "moderate"
        
        # Adjust based on user fitness level
        if user_profile and user_profile.fitness_level:
            fitness_level = user_profile.fitness_level
            if fitness_level == "beginner":
                if condition_intensity == "moderate":
                    return "low_to_moderate"
                elif condition_intensity == "high":
                    return "moderate"
            elif fitness_level == "advanced":
                if condition_intensity == "low":
                    return "low_to_moderate"
                elif condition_intensity == "moderate":
                    return "moderate_to_high"
        
        return condition_intensity
    
    def _generate_reasoning(self, exercise: HealthExercise, condition: DiseaseCondition,
                          effectiveness: float, safety: float) -> str:
        """Generate AI reasoning for the recommendation"""
        
        reasoning_parts = []
        
        # Exercise benefits for condition
        reasoning_parts.append(f"{exercise.name} is recommended for {condition.name} because it provides {', '.join(exercise.primary_benefits[:3])}.")
        
        # Safety considerations
        if safety >= 0.9:
            reasoning_parts.append("This exercise has an excellent safety profile for your condition.")
        elif safety >= 0.8:
            reasoning_parts.append("This exercise is considered safe when performed correctly.")
        
        # Effectiveness
        if effectiveness >= 0.8:
            reasoning_parts.append("Research shows this exercise is highly effective for managing your condition.")
        elif effectiveness >= 0.7:
            reasoning_parts.append("This exercise has shown good results for people with similar conditions.")
        
        # Special considerations
        if condition.special_considerations:
            reasoning_parts.append(f"Important: {condition.special_considerations}")
        
        return " ".join(reasoning_parts)
    
    def _determine_expected_benefits(self, exercise: HealthExercise, condition: DiseaseCondition) -> List[str]:
        """Determine expected benefits for user"""
        benefits = exercise.primary_benefits.copy() if exercise.primary_benefits else []
        
        # Add condition-specific benefits
        condition_benefits = {
            "cardiovascular": ["improved_heart_health", "better_circulation", "lower_blood_pressure"],
            "musculoskeletal": ["increased_strength", "better_flexibility", "reduced_pain"],
            "respiratory": ["improved_lung_function", "better_breathing", "increased_endurance"],
            "metabolic": ["weight_management", "better_glucose_control", "increased_metabolism"],
            "mental_health": ["mood_improvement", "stress_reduction", "better_sleep"]
        }
        
        if condition.category in condition_benefits:
            benefits.extend(condition_benefits[condition.category])
        
        return list(set(benefits))  # Remove duplicates
    
    def _determine_modifications(self, exercise: HealthExercise, condition: DiseaseCondition,
                               user_profile: Optional[UserHealthAnalysisProfile]) -> List[str]:
        """Determine necessary modifications"""
        modifications = []
        
        # Add exercise's built-in modifications
        if exercise.modifications:
            modifications.extend(exercise.modifications)
        
        # Add condition-specific modifications
        if "avoid_high_impact" in (condition.exercise_restrictions or []):
            modifications.append("Use low-impact variations")
        
        if "joint_protection" in (condition.exercise_restrictions or []):
            modifications.append("Focus on joint-friendly movements")
        
        if condition.requires_medical_clearance:
            modifications.append("Obtain medical clearance before starting")
        
        return modifications
    
    def _format_recommendation(self, recommendation: PersonalizedExerciseRecommendation) -> Dict:
        """Format recommendation for API response"""
        return {
            "id": recommendation.id,
            "exercise": {
                "id": recommendation.exercise.id,
                "name": recommendation.exercise.name,
                "category": recommendation.exercise.category.value,
                "difficulty_level": recommendation.exercise.difficulty_level.value,
                "description": recommendation.exercise.description,
                "instructions": recommendation.exercise.instructions,
                "equipment_needed": recommendation.exercise.equipment_needed,
                "primary_benefits": recommendation.exercise.primary_benefits,
                "safety_tips": recommendation.exercise.safety_tips,
                "video_url": recommendation.exercise.video_url,
                "image_url": recommendation.exercise.image_url
            },
            "condition": {
                "id": recommendation.condition.id,
                "name": recommendation.condition.name,
                "category": recommendation.condition.category
            },
            "personalization": {
                "recommended_duration": recommendation.recommended_duration,
                "recommended_frequency": recommendation.recommended_frequency.value if recommendation.recommended_frequency else None,
                "recommended_intensity": recommendation.recommended_intensity,
                "modifications_applied": recommendation.modifications_applied,
                "expected_benefits": recommendation.expected_benefits
            },
            "reasoning": recommendation.reasoning,
            "priority_score": recommendation.priority_score,
            "status": recommendation.status.value,
            "created_at": recommendation.created_at.isoformat() if recommendation.created_at else None
        }
    
    def get_user_recommendations(self, user_id: int, status: Optional[str] = None) -> List[Dict]:
        """Get user's exercise recommendations"""
        query = self.db.query(PersonalizedExerciseRecommendation).filter(
            PersonalizedExerciseRecommendation.user_id == user_id
        )
        
        if status:
            query = query.filter(PersonalizedExerciseRecommendation.status == RecommendationStatus(status))
        
        recommendations = query.order_by(PersonalizedExerciseRecommendation.priority_score.desc()).all()
        
        return [self._format_recommendation(rec) for rec in recommendations]
    
    def update_recommendation_feedback(self, recommendation_id: int, feedback_data: Dict) -> Dict:
        """Update recommendation with user feedback"""
        recommendation = self.db.query(PersonalizedExerciseRecommendation).filter(
            PersonalizedExerciseRecommendation.id == recommendation_id
        ).first()
        
        if not recommendation:
            raise ValueError("Recommendation not found")
        
        # Update feedback fields
        if 'user_rating' in feedback_data:
            recommendation.user_rating = feedback_data['user_rating']
        
        if 'user_feedback' in feedback_data:
            recommendation.user_feedback = feedback_data['user_feedback']
        
        if 'difficulty_feedback' in feedback_data:
            recommendation.difficulty_feedback = feedback_data['difficulty_feedback']
        
        if 'status' in feedback_data:
            recommendation.status = RecommendationStatus(feedback_data['status'])
        
        recommendation.updated_at = datetime.utcnow()
        self.db.commit()
        
        return self._format_recommendation(recommendation)