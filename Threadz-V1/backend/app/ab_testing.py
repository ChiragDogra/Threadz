"""
A/B Testing Framework for Threadz Application
"""
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from fastapi import HTTPException, status
from pydantic import BaseModel
from enum import Enum
import hashlib

from . import models, auth
from .database import get_db
from .sentry_config import sentry_manager
from .config import settings

class ExperimentStatus(str, Enum):
    """Experiment status"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class VariantType(str, Enum):
    """Variant types"""
    CONTROL = "control"
    TREATMENT = "treatment"

# Pydantic models
class ExperimentCreate(BaseModel):
    name: str
    description: str
    hypothesis: str
    variants: List[Dict[str, Any]]  # List of variant configurations
    traffic_split: float  # Percentage of traffic to include (0-100)
    success_metrics: List[str]  # Metrics to track
    target_audience: Optional[Dict[str, Any]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ExperimentResponse(BaseModel):
    experiment_id: str
    name: str
    description: str
    status: ExperimentStatus
    variants: List[Dict[str, Any]]
    traffic_split: float
    success_metrics: List[str]
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    results: Optional[Dict[str, Any]]

class ABTestingService:
    """A/B testing service for feature experimentation"""
    
    def __init__(self):
        self.experiments_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Default experiment configurations
        self.default_variants = {
            "button_color": ["#3b82f6", "#ef4444", "#10b981", "#f59e0b"],
            "pricing_display": ["standard", "discounted", "premium"],
            "ai_prompt_style": ["simple", "detailed", "creative"],
            "onboarding_flow": ["standard", "simplified", "interactive"]
        }
    
    def _generate_user_hash(self, user_id: str, experiment_id: str) -> str:
        """Generate consistent hash for user assignment"""
        combined = f"{user_id}:{experiment_id}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _assign_variant(self, user_hash: str, variants: List[Dict[str, Any]]) -> str:
        """Assign user to variant based on hash"""
        if not variants:
            return "control"
        
        # Use hash to determine variant
        hash_int = int(user_hash[:8], 16)
        variant_index = hash_int % len(variants)
        return variants[variant_index].get("id", f"variant_{variant_index}")
    
    async def create_experiment(
        self,
        experiment_data: ExperimentCreate,
        db: AsyncSession,
        current_user: models.User
    ) -> str:
        """Create a new A/B test experiment"""
        try:
            # Validate experiment data
            if not experiment_data.variants or len(experiment_data.variants) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Experiment must have at least 2 variants"
                )
            
            if not (0 <= experiment_data.traffic_split <= 100):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Traffic split must be between 0 and 100"
                )
            
            # Create experiment record (would need Experiment model)
            experiment_id = str(uuid.uuid4())
            
            # Store experiment configuration (in production, would save to database)
            experiment_config = {
                "id": experiment_id,
                "name": experiment_data.name,
                "description": experiment_data.description,
                "hypothesis": experiment_data.hypothesis,
                "variants": experiment_data.variants,
                "traffic_split": experiment_data.traffic_split,
                "success_metrics": experiment_data.success_metrics,
                "target_audience": experiment_data.target_audience,
                "start_date": experiment_data.start_date,
                "end_date": experiment_data.end_date,
                "status": ExperimentStatus.DRAFT,
                "created_at": datetime.utcnow(),
                "created_by": current_user.user_id
            }
            
            # Cache experiment
            self.experiments_cache[experiment_id] = experiment_config
            
            sentry_manager.add_tag("ab_test_created", experiment_id)
            sentry_manager.add_extra("experiment_name", experiment_data.name)
            
            return experiment_id
            
        except HTTPException:
            raise
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "create_experiment"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create experiment"
            )
    
    async def get_user_variant(
        self,
        user_id: str,
        experiment_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get the variant assigned to a user for an experiment"""
        try:
            # Get experiment configuration
            experiment = self.experiments_cache.get(experiment_id)
            if not experiment:
                return None
            
            # Check if experiment is running
            if experiment["status"] != ExperimentStatus.RUNNING:
                return None
            
            # Check if user is in target audience (simplified)
            if experiment["target_audience"]:
                # Would implement audience filtering logic here
                pass
            
            # Check traffic split
            user_hash = self._generate_user_hash(user_id, experiment_id)
            hash_int = int(user_hash[:8], 16)
            traffic_threshold = (hash_int % 100)
            
            if traffic_threshold > experiment["traffic_split"]:
                return None  # User not included in experiment
            
            # Assign variant
            variant_id = self._assign_variant(user_hash, experiment["variants"])
            
            # Find variant configuration
            variant_config = None
            for variant in experiment["variants"]:
                if variant.get("id") == variant_id:
                    variant_config = variant
                    break
            
            if not variant_config:
                return None
            
            # Record assignment (in production, would save to database)
            assignment_data = {
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "assigned_at": datetime.utcnow()
            }
            
            return {
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "config": variant_config,
                "is_control": variant_id == "control"
            }
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "get_user_variant",
                "user_id": user_id,
                "experiment_id": experiment_id
            })
            return None
    
    async def track_conversion(
        self,
        user_id: str,
        experiment_id: str,
        metric: str,
        value: float = 1.0,
        db: AsyncSession
    ) -> bool:
        """Track conversion event for A/B test"""
        try:
            # Get user's variant assignment
            variant = await self.get_user_variant(user_id, experiment_id, db)
            if not variant:
                return False
            
            # Check if metric is tracked for this experiment
            experiment = self.experiments_cache.get(experiment_id)
            if not experiment or metric not in experiment["success_metrics"]:
                return False
            
            # Record conversion (in production, would save to database)
            conversion_data = {
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant_id": variant["variant_id"],
                "metric": metric,
                "value": value,
                "timestamp": datetime.utcnow()
            }
            
            sentry_manager.add_tag("ab_test_conversion", experiment_id)
            sentry_manager.add_extra("variant_id", variant["variant_id"])
            sentry_manager.add_extra("metric", metric)
            
            return True
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "track_conversion",
                "user_id": user_id,
                "experiment_id": experiment_id
            })
            return False
    
    async def get_experiment_results(
        self,
        experiment_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get results for an experiment"""
        try:
            experiment = self.experiments_cache.get(experiment_id)
            if not experiment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Experiment not found"
                )
            
            # Mock results (in production, would calculate from actual data)
            results = {
                "experiment_id": experiment_id,
                "status": experiment["status"],
                "variants": [],
                "metrics": {},
                "statistical_significance": False,
                "winner": None
            }
            
            # Generate mock results for each variant
            for variant in experiment["variants"]:
                variant_id = variant.get("id")
                variant_results = {
                    "variant_id": variant_id,
                    "name": variant.get("name", variant_id),
                    "conversions": 0,
                    "conversion_rate": 0.0,
                    "users": 0,
                    "revenue": 0.0
                }
                
                # Mock data
                if variant_id == "control":
                    variant_results["conversions"] = 150
                    variant_results["users"] = 1000
                    variant_results["revenue"] = 7500.0
                else:
                    variant_results["conversions"] = 180
                    variant_results["users"] = 980
                    variant_results["revenue"] = 8100.0
                
                variant_results["conversion_rate"] = (variant_results["conversions"] / variant_results["users"]) * 100
                results["variants"].append(variant_results)
            
            # Calculate metrics
            for metric in experiment["success_metrics"]:
                results["metrics"][metric] = {
                    "control_value": 15.0,
                    "treatment_value": 18.4,
                    "lift": 22.7,
                    "confidence": 95.2
                }
            
            # Determine winner
            best_variant = max(results["variants"], key=lambda x: x["conversion_rate"])
            results["winner"] = best_variant["variant_id"]
            results["statistical_significance"] = True
            
            return results
            
        except HTTPException:
            raise
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "get_experiment_results",
                "experiment_id": experiment_id
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get experiment results"
            )
    
    async def list_experiments(
        self,
        status_filter: Optional[ExperimentStatus] = None,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """List all experiments"""
        try:
            experiments = []
            
            for exp_id, exp_config in self.experiments_cache.items():
                if status_filter and exp_config["status"] != status_filter:
                    continue
                
                experiments.append({
                    "experiment_id": exp_id,
                    "name": exp_config["name"],
                    "description": exp_config["description"],
                    "status": exp_config["status"],
                    "created_at": exp_config["created_at"],
                    "variants_count": len(exp_config["variants"]),
                    "traffic_split": exp_config["traffic_split"]
                })
            
            return sorted(experiments, key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "list_experiments"})
            return []
    
    async def start_experiment(
        self,
        experiment_id: str,
        db: AsyncSession,
        current_user: models.User
    ) -> bool:
        """Start an experiment"""
        try:
            experiment = self.experiments_cache.get(experiment_id)
            if not experiment:
                return False
            
            if experiment["status"] != ExperimentStatus.DRAFT:
                return False
            
            # Update experiment status
            experiment["status"] = ExperimentStatus.RUNNING
            experiment["started_at"] = datetime.utcnow()
            
            sentry_manager.add_tag("ab_test_started", experiment_id)
            
            return True
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "start_experiment",
                "experiment_id": experiment_id
            })
            return False
    
    async def stop_experiment(
        self,
        experiment_id: str,
        db: AsyncSession,
        current_user: models.User
    ) -> bool:
        """Stop an experiment"""
        try:
            experiment = self.experiments_cache.get(experiment_id)
            if not experiment:
                return False
            
            if experiment["status"] != ExperimentStatus.RUNNING:
                return False
            
            # Update experiment status
            experiment["status"] = ExperimentStatus.COMPLETED
            experiment["ended_at"] = datetime.utcnow()
            
            sentry_manager.add_tag("ab_test_stopped", experiment_id)
            
            return True
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "stop_experiment",
                "experiment_id": experiment_id
            })
            return False

# Global A/B testing service instance
ab_testing_service = ABTestingService()

# Middleware for A/B testing
async def ab_testing_middleware(request: Request, call_next):
    """Middleware to handle A/B testing assignments"""
    # Get user ID from request (if authenticated)
    user_id = None
    if hasattr(request.state, 'user'):
        user_id = request.state.user.user_id
    
    # Check for active experiments and assign variants
    if user_id:
        # This would check for active experiments and assign variants
        pass
    
    response = await call_next(request)
    
    # Add A/B testing headers
    # response.headers["X-AB-Test-Variant"] = variant_id
    
    return response

# Feature flag helper
async def get_feature_flag(
    feature_name: str,
    user_id: Optional[str] = None,
    default_value: bool = False
) -> bool:
    """Get feature flag value (simplified A/B testing)"""
    try:
        # In production, would check feature flag service
        # For now, return default value
        return default_value
        
    except Exception as e:
        sentry_manager.capture_exception(e, {
            "action": "get_feature_flag",
            "feature_name": feature_name
        })
        return default_value
