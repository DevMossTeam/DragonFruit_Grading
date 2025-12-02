from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import get_db
from models.grading_model import GradingResult

router = APIRouter(prefix="/api/vision-features", tags=["vision-features"])

@router.get("/statistics")
async def get_vision_features_statistics(db: Session = Depends(get_db)):
    """
    Fetch computer vision feature statistics from the grading_results table.
    Returns extracted features: length_cm, diameter_cm, weight_est_g, ratio
    """
    try:
        # Query all grading results with vision features
        results = db.query(GradingResult).filter(
            GradingResult.length_cm.isnot(None),
            GradingResult.diameter_cm.isnot(None),
            GradingResult.weight_est_g.isnot(None),
            GradingResult.ratio.isnot(None)
        ).all()

        if not results:
            return {
                'status': 'no_data',
                'message': 'No vision features data found in database',
                'has_data': False,
                'total_samples': 0
            }

        # Group data by final_grade
        features_by_grade = {'A': [], 'B': [], 'C': []}
        all_features = []

        for result in results:
            feature_dict = {
                'id': str(result.id),
                'grade': result.final_grade or 'Unknown',
                'length_cm': float(result.length_cm) if result.length_cm else 0,
                'diameter_cm': float(result.diameter_cm) if result.diameter_cm else 0,
                'weight_est_g': float(result.weight_est_g) if result.weight_est_g else 0,
                'ratio': float(result.ratio) if result.ratio else 0,
            }
            all_features.append(feature_dict)

            if result.final_grade in features_by_grade:
                features_by_grade[result.final_grade].append(feature_dict)

        # Calculate statistics for each grade
        stats_response = {}
        for grade, data in features_by_grade.items():
            if data:
                lengths = [d['length_cm'] for d in data if d['length_cm'] > 0]
                diameters = [d['diameter_cm'] for d in data if d['diameter_cm'] > 0]
                weights = [d['weight_est_g'] for d in data if d['weight_est_g'] > 0]
                ratios = [d['ratio'] for d in data if d['ratio'] > 0]

                stats_response[grade] = {
                    'count': len(data),
                    'length': {
                        'min': min(lengths) if lengths else 0,
                        'max': max(lengths) if lengths else 0,
                        'avg': sum(lengths) / len(lengths) if lengths else 0,
                    },
                    'diameter': {
                        'min': min(diameters) if diameters else 0,
                        'max': max(diameters) if diameters else 0,
                        'avg': sum(diameters) / len(diameters) if diameters else 0,
                    },
                    'weight': {
                        'min': min(weights) if weights else 0,
                        'max': max(weights) if weights else 0,
                        'avg': sum(weights) / len(weights) if weights else 0,
                    },
                    'ratio': {
                        'min': min(ratios) if ratios else 0,
                        'max': max(ratios) if ratios else 0,
                        'avg': sum(ratios) / len(ratios) if ratios else 0,
                    }
                }

        total_count = sum([len(features_by_grade[g]) for g in ['A', 'B', 'C']])

        return {
            'status': 'success',
            'message': 'Computer vision features retrieved successfully',
            'total_samples': total_count,
            'stats': stats_response,
            'has_data': True
        }

    except Exception as e:
        print(f"Error fetching vision features: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching vision features: {str(e)}"
        )


@router.get("/distribution")
async def get_vision_features_distribution(db: Session = Depends(get_db)):
    """
    Get distribution of vision features for charts (min, avg, max for each grade)
    """
    try:
        results = db.query(GradingResult).filter(
            GradingResult.length_cm.isnot(None),
            GradingResult.diameter_cm.isnot(None),
            GradingResult.weight_est_g.isnot(None),
            GradingResult.ratio.isnot(None)
        ).all()

        if not results:
            return {
                'status': 'no_data',
                'has_data': False
            }

        # Group by grade
        grouped = {'A': [], 'B': [], 'C': []}
        for result in results:
            if result.final_grade in grouped:
                grouped[result.final_grade].append({
                    'length': float(result.length_cm) if result.length_cm else 0,
                    'diameter': float(result.diameter_cm) if result.diameter_cm else 0,
                    'weight': float(result.weight_est_g) if result.weight_est_g else 0,
                    'ratio': float(result.ratio) if result.ratio else 0,
                })

        # Calculate distributions
        distribution = {}
        for grade in ['A', 'B', 'C']:
            data = grouped[grade]
            if data:
                lengths = [d['length'] for d in data if d['length'] > 0]
                diameters = [d['diameter'] for d in data if d['diameter'] > 0]
                weights = [d['weight'] for d in data if d['weight'] > 0]
                ratios = [d['ratio'] for d in data if d['ratio'] > 0]

                distribution[grade] = {
                    'length': {
                        'min': min(lengths) if lengths else 0,
                        'avg': sum(lengths) / len(lengths) if lengths else 0,
                        'max': max(lengths) if lengths else 0,
                    },
                    'diameter': {
                        'min': min(diameters) if diameters else 0,
                        'avg': sum(diameters) / len(diameters) if diameters else 0,
                        'max': max(diameters) if diameters else 0,
                    },
                    'weight': {
                        'min': min(weights) if weights else 0,
                        'avg': sum(weights) / len(weights) if weights else 0,
                        'max': max(weights) if weights else 0,
                    },
                    'ratio': {
                        'min': min(ratios) if ratios else 0,
                        'avg': sum(ratios) / len(ratios) if ratios else 0,
                        'max': max(ratios) if ratios else 0,
                    }
                }

        return {
            'status': 'success',
            'has_data': True,
            'distribution': distribution
        }

    except Exception as e:
        print(f"Error fetching vision features distribution: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@router.get("/weight-comparison")
async def get_weight_comparison(db: Session = Depends(get_db)):
    """
    Get weight comparison between actual weight (from sensor) and estimated weight (from vision).
    Groups by grade and calculates statistics for both.
    """
    try:
        # Query all grading results with weight data
        results = db.query(GradingResult).filter(
            (GradingResult.weight_est_g.isnot(None)) | (GradingResult.weight_actual_g.isnot(None))
        ).all()

        if not results:
            return {
                'status': 'no_data',
                'message': 'No weight data found in database',
                'has_data': False,
                'total_samples': 0
            }

        # Filter only records with both actual and estimated weight
        valid_results = [r for r in results if r.weight_actual_g is not None and r.weight_est_g is not None]

        if not valid_results:
            return {
                'status': 'no_data',
                'message': 'No records with both actual and estimated weight',
                'has_data': False,
                'total_samples': 0
            }

        # Group by grade
        weight_by_grade = {'A': [], 'B': [], 'C': []}
        
        for result in valid_results:
            weight_pair = {
                'actual': float(result.weight_actual_g),
                'estimated': float(result.weight_est_g),
                'error': abs(float(result.weight_actual_g) - float(result.weight_est_g))
            }
            if result.final_grade in weight_by_grade:
                weight_by_grade[result.final_grade].append(weight_pair)

        # Calculate statistics for each grade
        stats_response = {}
        for grade, data in weight_by_grade.items():
            if data:
                actual_weights = [d['actual'] for d in data]
                estimated_weights = [d['estimated'] for d in data]
                errors = [d['error'] for d in data]

                stats_response[grade] = {
                    'count': len(data),
                    'actual_weight': {
                        'min': min(actual_weights),
                        'max': max(actual_weights),
                        'avg': sum(actual_weights) / len(actual_weights),
                    },
                    'estimated_weight': {
                        'min': min(estimated_weights),
                        'max': max(estimated_weights),
                        'avg': sum(estimated_weights) / len(estimated_weights),
                    },
                    'error': {
                        'min': min(errors),
                        'max': max(errors),
                        'avg': sum(errors) / len(errors),
                    }
                }

        total_count = sum([len(weight_by_grade[g]) for g in ['A', 'B', 'C']])

        return {
            'status': 'success',
            'message': 'Weight comparison data retrieved successfully',
            'total_samples': total_count,
            'stats': stats_response,
            'has_data': True
        }

    except Exception as e:
        print(f"Error fetching weight comparison: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching weight comparison: {str(e)}"
        )
