"""
Metrics Service for Classification Evaluation
Computes accuracy, precision, recall, F1-score, and confusion matrix
"""

import requests
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class MetricsService:
    """Service to compute classification metrics from grading results"""
    
    VALID_GRADES = ["A", "B", "C"]
    API_ENDPOINT = "http://127.0.0.1:8000/api/gradingresult/all"
    
    # Weight-based grading thresholds (in grams)
    WEIGHT_GRADE_THRESHOLDS = {
        "A": (350, float('inf')),      # >= 600g = Grade A (Premium)
        "B": (250, 350),                # 300-599g = Grade B (Regular)
        "C": (0, 250),                  # < 300g = Grade C (Small/Standard)
    }
    
    @staticmethod
    def grade_by_actual_weight(weight_g: float) -> str:
        """
        Classify dragon fruit grade based on actual weight (ground truth)
        
        Args:
            weight_g: Actual weight in grams
            
        Returns:
            Grade: 'A', 'B', or 'C'
        """
        if weight_g is None or weight_g < 0:
            return None
        
        for grade, (min_weight, max_weight) in MetricsService.WEIGHT_GRADE_THRESHOLDS.items():
            if min_weight <= weight_g < max_weight:
                return grade
        
        return None
    
    @staticmethod
    def fetch_grading_results() -> List[Dict[str, Any]]:
        """
        Fetch all grading results from the API
        
        Returns:
            List of grading result dictionaries
            
        Raises:
            Exception: If API call fails
        """
        try:
            response = requests.get(MetricsService.API_ENDPOINT, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("data", [])
            
            logger.info(f"Fetched {len(results)} grading results from API")
            return results
        except Exception as e:
            logger.error(f"Error fetching grading results: {str(e)}")
            raise
    
    @staticmethod
    def validate_grades(y_true: List[str], y_pred: List[str]) -> tuple:
        """
        Validate and filter grades, keeping only valid ones (A, B, C)
        
        Args:
            y_true: List of true labels (final_grade)
            y_pred: List of predicted labels (final_grade)
            
        Returns:
            Tuple of (filtered_y_true, filtered_y_pred)
        """
        valid_indices = []
        
        for i, (true_grade, pred_grade) in enumerate(zip(y_true, y_pred)):
            if true_grade in MetricsService.VALID_GRADES and pred_grade in MetricsService.VALID_GRADES:
                valid_indices.append(i)
        
        y_true_filtered = [y_true[i] for i in valid_indices]
        y_pred_filtered = [y_pred[i] for i in valid_indices]
        
        logger.info(f"Validated grades: {len(y_true_filtered)} out of {len(y_true)} records")
        
        return y_true_filtered, y_pred_filtered
    
    @staticmethod
    def compute_fuzzy_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute fuzzy logic metrics by comparing predicted grade vs actual grade
        
        Calculates:
        - Fuzzy Accuracy: Average confidence of all predictions
        - Fuzzy Precision: Per-grade TP / (TP + FP)
        - Fuzzy Recall: Per-grade TP / (TP + FN)
        - Fuzzy F1: Harmonic mean of precision and recall per grade
        
        Args:
            results: List of grading result dictionaries
            
        Returns:
            Dictionary containing fuzzy metrics
        """
        if not results:
            return {
                "fuzzy_accuracy": 0.0,
                "fuzzy_precision_A": 0.0,
                "fuzzy_precision_B": 0.0,
                "fuzzy_precision_C": 0.0,
                "fuzzy_recall_A": 0.0,
                "fuzzy_recall_B": 0.0,
                "fuzzy_recall_C": 0.0,
                "fuzzy_f1_A": 0.0,
                "fuzzy_f1_B": 0.0,
                "fuzzy_f1_C": 0.0,
            }
        
        # Fuzzy Accuracy: Average of all fuzzy scores (confidence metric)
        fuzzy_scores = [r.get("fuzzy_score", 0) for r in results if r.get("fuzzy_score") is not None]
        
        if not fuzzy_scores:
            fuzzy_accuracy = 0.0
        else:
            # Normalize fuzzy scores to 0-1 if they're in 0-100 range
            avg_fuzzy = sum(fuzzy_scores) / len(fuzzy_scores)
            fuzzy_accuracy = avg_fuzzy / 100 if avg_fuzzy > 1 else avg_fuzzy
        
        # Calculate ground truth grades from weight_actual_g
        y_true = []
        y_pred = []
        
        for r in results:
            weight_actual = r.get("weight_actual_g")
            predicted_grade = r.get("final_grade")
            
            if weight_actual is not None and predicted_grade:
                # Calculate actual grade from weight (ground truth)
                actual_grade = MetricsService.grade_by_actual_weight(weight_actual)
                
                if actual_grade:
                    y_true.append(actual_grade)
                    y_pred.append(predicted_grade)
        
        # Per-grade Precision, Recall, and F1 using confusion matrix approach
        grades = {}
        total_samples = len(y_true)
        
        for grade in MetricsService.VALID_GRADES:
            # True Positives: Correctly predicted as this grade
            tp = sum(1 for true, pred in zip(y_true, y_pred) if true == grade and pred == grade)
            
            # False Positives: Incorrectly predicted as this grade
            fp = sum(1 for true, pred in zip(y_true, y_pred) if true != grade and pred == grade)
            
            # False Negatives: Should have been this grade but wasn't
            fn = sum(1 for true, pred in zip(y_true, y_pred) if true == grade and pred != grade)
            
            # Precision = TP / (TP + FP)
            # How many predicted as this grade are actually correct?
            if tp + fp > 0:
                precision = tp / (tp + fp)
            else:
                precision = 0.0
            
            # Recall = TP / (TP + FN)
            # Of all actual samples of this grade, how many did we correctly identify?
            if tp + fn > 0:
                recall = tp / (tp + fn)
            else:
                recall = 0.0
            
            # F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
            if precision + recall > 0:
                f1 = 2 * (precision * recall) / (precision + recall)
            else:
                f1 = 0.0
            
            grades[f"fuzzy_precision_{grade}"] = round(precision, 4)
            grades[f"fuzzy_recall_{grade}"] = round(recall, 4)
            grades[f"fuzzy_f1_{grade}"] = round(f1, 4)
        
        return {
            "fuzzy_accuracy": round(fuzzy_accuracy, 4),
            **grades
        }
    
    @staticmethod
    def compute_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, Any]:
        """
        Compute comprehensive classification metrics
        
        Args:
            y_true: List of true labels
            y_pred: List of predicted labels
            
        Returns:
            Dictionary containing all metrics
        """
        if not y_true or not y_pred:
            logger.warning("No valid grades to compute metrics")
            return {
                "accuracy": 0,
                "precision_A": 0, "precision_B": 0, "precision_C": 0,
                "recall_A": 0, "recall_B": 0, "recall_C": 0,
                "f1_A": 0, "f1_B": 0, "f1_C": 0,
                "macro_precision": 0, "macro_recall": 0, "macro_f1": 0,
                "weighted_f1": 0,
                "confusion_matrix": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
                "total_samples": 0,
                "valid_samples": 0
            }
        
        # Overall metrics
        accuracy = accuracy_score(y_true, y_pred)
        macro_precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
        macro_recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
        macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
        weighted_f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        # Per-class metrics
        metrics = {
            "accuracy": round(float(accuracy), 4),
            "macro_precision": round(float(macro_precision), 4),
            "macro_recall": round(float(macro_recall), 4),
            "macro_f1": round(float(macro_f1), 4),
            "weighted_f1": round(float(weighted_f1), 4),
            "total_samples": len(y_true),
            "valid_samples": len(y_true),
        }
        
        # Per-class metrics (A, B, C)
        for grade in MetricsService.VALID_GRADES:
            try:
                precision = precision_score(y_true, y_pred, labels=[grade], average=None, zero_division=0)[0]
                recall = recall_score(y_true, y_pred, labels=[grade], average=None, zero_division=0)[0]
                f1 = f1_score(y_true, y_pred, labels=[grade], average=None, zero_division=0)[0]
                
                metrics[f"precision_{grade}"] = round(float(precision), 4)
                metrics[f"recall_{grade}"] = round(float(recall), 4)
                metrics[f"f1_{grade}"] = round(float(f1), 4)
            except Exception as e:
                logger.warning(f"Error computing metrics for grade {grade}: {str(e)}")
                metrics[f"precision_{grade}"] = 0
                metrics[f"recall_{grade}"] = 0
                metrics[f"f1_{grade}"] = 0
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=MetricsService.VALID_GRADES)
        cm_list = cm.tolist()
        
        metrics["confusion_matrix"] = cm_list
        
        logger.info(f"Computed metrics - Accuracy: {accuracy:.4f}, Macro F1: {macro_f1:.4f}")
        
        return metrics
    
    @staticmethod
    def get_all_metrics() -> Dict[str, Any]:
        """
        Main method: Fetch data, validate, and compute metrics
        
        Compares:
        - y_true: Ground truth grade from actual weight (weight_actual_g)
        - y_pred: Fuzzy logic prediction (final_grade)
        
        Also computes fuzzy metrics based on fuzzy_score confidence
        
        Returns:
            Dictionary with all metrics and metadata
        """
        try:
            # Fetch data
            results = MetricsService.fetch_grading_results()
            
            if not results:
                # Return default metrics with 0 values
                return {
                    "status": "warning",
                    "message": "No grading results found",
                    "metrics": {
                        "accuracy": 0,
                        "precision_A": 0, "precision_B": 0, "precision_C": 0,
                        "recall_A": 0, "recall_B": 0, "recall_C": 0,
                        "f1_A": 0, "f1_B": 0, "f1_C": 0,
                        "macro_precision": 0, "macro_recall": 0, "macro_f1": 0,
                        "weighted_f1": 0,
                        "confusion_matrix": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
                        "total_samples": 0,
                        "valid_samples": 0,
                        "fuzzy_accuracy": 0,
                        "fuzzy_precision_A": 0, "fuzzy_precision_B": 0, "fuzzy_precision_C": 0,
                        "fuzzy_recall_A": 0, "fuzzy_recall_B": 0, "fuzzy_recall_C": 0,
                        "fuzzy_f1_A": 0, "fuzzy_f1_B": 0, "fuzzy_f1_C": 0,
                    }
                }
            
            # Compute fuzzy metrics (based on fuzzy_score, no ground truth needed)
            fuzzy_metrics = MetricsService.compute_fuzzy_metrics(results)
            
            # Extract grades for accuracy metrics
            # y_true: Ground truth from actual weight (weight_actual_g)
            # y_pred: Fuzzy logic predictions (final_grade)
            y_true = []
            y_pred = []
            
            for r in results:
                actual_weight = r.get("weight_actual_g")
                predicted_grade = r.get("final_grade")
                
                # Calculate true grade from actual weight
                true_grade = MetricsService.grade_by_actual_weight(actual_weight)
                
                # Only include if we have both actual weight and prediction
                if true_grade is not None and predicted_grade is not None:
                    y_true.append(true_grade)
                    y_pred.append(predicted_grade)
            
            logger.info(f"Extracted {len(y_true)} valid samples for validation (actual weight available)")
            
            # Compute classification metrics if we have ground truth
            if y_true and y_pred:
                # Validate
                y_true_valid, y_pred_valid = MetricsService.validate_grades(y_true, y_pred)
                
                if y_true_valid and y_pred_valid:
                    # Compute metrics
                    metrics = MetricsService.compute_metrics(y_true_valid, y_pred_valid)
                    # Merge fuzzy metrics into main metrics
                    metrics.update(fuzzy_metrics)
                    
                    return {
                        "status": "success",
                        "message": f"Metrics computed successfully - Compared {len(y_true_valid)} fuzzy predictions against weight-based ground truth",
                        "metrics": metrics,
                        "timestamp": pd.Timestamp.now().isoformat()
                    }
            
            # If no ground truth, just return fuzzy metrics
            default_metrics = {
                "accuracy": 0,
                "precision_A": 0, "precision_B": 0, "precision_C": 0,
                "recall_A": 0, "recall_B": 0, "recall_C": 0,
                "f1_A": 0, "f1_B": 0, "f1_C": 0,
                "macro_precision": 0, "macro_recall": 0, "macro_f1": 0,
                "weighted_f1": 0,
                "confusion_matrix": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
                "total_samples": len(results),
                "valid_samples": len(y_true) if y_true else 0,
            }
            default_metrics.update(fuzzy_metrics)
            
            return {
                "status": "success",
                "message": f"Fuzzy metrics computed for {len(results)} samples (ground truth not available for accuracy)",
                "metrics": default_metrics,
                "timestamp": pd.Timestamp.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error in get_all_metrics: {str(e)}")
            return {
                "status": "error",
                "message": f"Error computing metrics: {str(e)}",
                "metrics": None
            }
