from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime
from database.config import get_sync_db
from database.models import User, UserProfile, FitnessLevel, Gender
from auth.auth import current_active_user
import json

router = APIRouter(prefix="/profile", tags=["profiles"])

# Pydantic models for API
class ProfileCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    fitness_level: Optional[str] = "beginner"
    medical_conditions: Optional[List[str]] = []
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = {}
    timezone: Optional[str] = "UTC"
    language: Optional[str] = "en"
    activity_goals: Optional[Dict[str, Any]] = {}
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v
    
    @validator('weight')
    def validate_weight(cls, v):
        if v is not None and (v < 0 or v > 1000):
            raise ValueError('Weight must be between 0 and 1000 kg')
        return v
    
    @validator('height')
    def validate_height(cls, v):
        if v is not None and (v < 0 or v > 300):
            raise ValueError('Height must be between 0 and 300 cm')
        return v
    
    @validator('fitness_level')
    def validate_fitness_level(cls, v):
        if v is not None:
            valid_levels = [level.value for level in FitnessLevel]
            if v not in valid_levels:
                raise ValueError(f'Fitness level must be one of: {valid_levels}')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        if v is not None:
            valid_genders = [gender.value for gender in Gender]
            if v not in valid_genders:
                raise ValueError(f'Gender must be one of: {valid_genders}')
        return v

class ProfileUpdate(ProfileCreate):
    pass

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    first_name: Optional[str]
    last_name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    weight: Optional[float]
    height: Optional[float]
    bmi: Optional[float]
    fitness_level: Optional[str]
    medical_conditions: Optional[List[str]]
    allergies: Optional[str]
    medications: Optional[str]
    emergency_contact: Optional[str]
    preferences: Optional[Dict[str, Any]]
    timezone: Optional[str]
    language: Optional[str]
    activity_goals: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class HealthMetrics(BaseModel):
    bmi: Optional[float]
    bmi_category: Optional[str]
    ideal_weight_range: Optional[Dict[str, float]]
    daily_calorie_needs: Optional[int]
    recommended_water_intake: Optional[float]

# Helper functions
def calculate_bmi(weight: float, height: float) -> float:
    """Calculate BMI from weight (kg) and height (cm)"""
    if not weight or not height or height == 0:
        return None
    height_m = height / 100  # Convert cm to meters
    return round(weight / (height_m ** 2), 2)

def get_bmi_category(bmi: float) -> str:
    """Get BMI category based on BMI value"""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def calculate_ideal_weight_range(height: float) -> Dict[str, float]:
    """Calculate ideal weight range based on height"""
    if not height:
        return None
    height_m = height / 100
    min_weight = round(18.5 * (height_m ** 2), 1)
    max_weight = round(24.9 * (height_m ** 2), 1)
    return {"min": min_weight, "max": max_weight}

def calculate_daily_calories(weight: float, height: float, age: int, gender: str, fitness_level: str) -> int:
    """Calculate daily calorie needs using Mifflin-St Jeor Equation"""
    if not all([weight, height, age, gender]):
        return None
    
    # Base Metabolic Rate (BMR)
    if gender.lower() == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    # Activity multiplier based on fitness level
    activity_multipliers = {
        "beginner": 1.2,
        "intermediate": 1.55,
        "advanced": 1.725,
        "athlete": 1.9
    }
    
    multiplier = activity_multipliers.get(fitness_level, 1.2)
    return round(bmr * multiplier)

def calculate_water_intake(weight: float) -> float:
    """Calculate recommended daily water intake in liters"""
    if not weight:
        return None
    return round(weight * 0.035, 1)  # 35ml per kg of body weight

# API Endpoints
@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get current user's profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        # Create empty profile if doesn't exist
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return profile

@router.post("/me", response_model=ProfileResponse)
async def create_or_update_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Create or update current user's profile"""
    existing_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    # Calculate BMI if weight and height are provided
    bmi = None
    if profile_data.weight and profile_data.height:
        bmi = calculate_bmi(profile_data.weight, profile_data.height)
    
    profile_dict = profile_data.dict(exclude_unset=True)
    profile_dict['bmi'] = bmi
    
    # Convert enum strings to enum objects
    if 'fitness_level' in profile_dict and profile_dict['fitness_level']:
        profile_dict['fitness_level'] = FitnessLevel(profile_dict['fitness_level'])
    
    if 'gender' in profile_dict and profile_dict['gender']:
        profile_dict['gender'] = Gender(profile_dict['gender'])
    
    if existing_profile:
        # Update existing profile
        for key, value in profile_dict.items():
            if value is not None:
                setattr(existing_profile, key, value)
        
        db.commit()
        db.refresh(existing_profile)
        return existing_profile
    else:
        # Create new profile
        profile_dict['user_id'] = current_user.id
        new_profile = UserProfile(**profile_dict)
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        return new_profile

@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Update current user's profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Calculate BMI if weight and height are provided
    update_data = profile_data.dict(exclude_unset=True)
    
    if ('weight' in update_data or 'height' in update_data):
        weight = update_data.get('weight', profile.weight)
        height = update_data.get('height', profile.height)
        if weight and height:
            update_data['bmi'] = calculate_bmi(weight, height)
    
    # Convert enum strings to enum objects
    if 'fitness_level' in update_data and update_data['fitness_level']:
        update_data['fitness_level'] = FitnessLevel(update_data['fitness_level'])
    
    if 'gender' in update_data and update_data['gender']:
        update_data['gender'] = Gender(update_data['gender'])
    
    # Update profile
    for key, value in update_data.items():
        if value is not None:
            setattr(profile, key, value)
    
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/me/health-metrics", response_model=HealthMetrics)
async def get_health_metrics(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get calculated health metrics for current user"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    metrics = HealthMetrics()
    
    if profile.weight and profile.height:
        bmi = calculate_bmi(profile.weight, profile.height)
        metrics.bmi = bmi
        metrics.bmi_category = get_bmi_category(bmi)
        metrics.ideal_weight_range = calculate_ideal_weight_range(profile.height)
        metrics.recommended_water_intake = calculate_water_intake(profile.weight)
        
        if profile.age and profile.gender and profile.fitness_level:
            metrics.daily_calorie_needs = calculate_daily_calories(
                profile.weight,
                profile.height,
                profile.age,
                profile.gender.value,
                profile.fitness_level.value
            )
    
    return metrics

@router.delete("/me")
async def delete_profile(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Delete current user's profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    db.delete(profile)
    db.commit()
    
    return {"message": "Profile deleted successfully"}

# Admin endpoints
@router.get("/admin/all", response_model=List[ProfileResponse])
async def get_all_profiles(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get all user profiles (admin only)"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    profiles = db.query(UserProfile).offset(skip).limit(limit).all()
    return profiles

@router.get("/admin/{user_id}", response_model=ProfileResponse)
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get specific user's profile (admin only)"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile
