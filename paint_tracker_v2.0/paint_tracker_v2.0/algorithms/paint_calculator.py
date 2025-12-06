"""
Paint mixing calculator - handles ratio calculations for interior/exterior jobs.
Uses the following ratios: 3:1:3 for interior, 3:1:1 for exterior.

This module is part of Enhancement Two (Algorithms and Data Structures) for the 
CS 499 capstone project. It demonstrates:
- Industry-standard paint mixing ratio calculations
- Algorithm implementation with proper data structures
- Coverage estimation calculations (future feature, not yet in UI)
- Input validation and error handling

Note: Coverage estimation is implemented but not exposed in the UI. It's kept
as a foundation for future features and demonstrates algorithm completeness.
"""

from typing import Dict, Tuple


class PaintMixCalculator:
    """
    Calculates paint mixing ratios for interior and exterior jobs.

    Interior formula: 3 parts paint : 1 part catalyst : 3 parts additive
    Exterior formula: 3 parts paint : 1 part catalyst : 1 part reducer
    """

    # Define the mixing ratios for each job type
    # Using dictionary format: {component_name: ratio_parts}
    MIXING_RATIOS = {
        'interior': {
            'paint': 3,
            'catalyst': 1,
            'additive': 3
        },
        'exterior': {
            'paint': 3,
            'catalyst': 1,
            'reducer': 1
        }
    }

    def calculate_mix(self, job_type: str, paint_amount: float) -> Dict[str, float]:
        """
        Calculate component amounts based on job type and paint amount.

        User specifies paint amount, this calculates catalyst and additive/reducer.
        Interior (3:1:3): catalyst = paint/3, additive = paint
        Exterior (3:1:1): catalyst = paint/3, reducer = paint/3
        """
        # Input validation
        if job_type.lower() not in ['interior', 'exterior']:
            raise ValueError(f"Job type must be 'interior' or 'exterior', got: {job_type}")

        if paint_amount <= 0:
            raise ValueError(f"Paint amount must be positive, got: {paint_amount}")

        job = job_type.lower()

        if job == 'interior':
            # Interior ratio 3:1:3 
            catalyst = paint_amount / 3
            additive = paint_amount  

            components = {
                'paint': round(paint_amount, 1),
                'catalyst': round(catalyst, 1),
                'additive': round(additive, 1)
            }
        else:  # exterior
            # Exterior ratio 3:1:1 
            catalyst = paint_amount / 3
            reducer = paint_amount / 3

            components = {
                'paint': round(paint_amount, 1),
                'catalyst': round(catalyst, 1),
                'reducer': round(reducer, 1)
            }

        return components

    def get_ratio_display(self, job_type: str) -> str:
        """Get ratio string for display (e.g., '3:1:3' or '3:1:1')"""
        if job_type.lower() not in ['interior', 'exterior']:
            return "Unknown ratio"

        if job_type.lower() == 'interior':
            return "3:1:3"
        else:
            return "3:1:1"

    def get_component_names(self, job_type: str) -> Tuple[str, ...]:
        """Get component names for a job type (paint, catalyst, third component)"""
        if job_type.lower() not in ['interior', 'exterior']:
            return ()

        ratio = self.MIXING_RATIOS[job_type.lower()]
        return tuple(ratio.keys())

    def validate_custom_amounts(self, job_type: str, components: Dict[str, float]) -> Tuple[bool, str]:
        """Check if manually entered amounts match the expected ratio."""
        if job_type.lower() not in ['interior', 'exterior']:
            return False, "Invalid job type"

        expected_ratio = self.MIXING_RATIOS[job_type.lower()]

        # Check all required components are present
        for component in expected_ratio.keys():
            if component not in components:
                return False, f"Missing component: {component}"

        # Calculate the ratios from provided amounts
        # Find the smallest amount and use it as the base unit
        min_amount = min(components.values())
        if min_amount <= 0:
            return False, "All amounts must be positive"

        # Calculate actual ratios by dividing by the smallest amount
        actual_ratios = {
            name: round(amount / min_amount, 1)
            for name, amount in components.items()
        }

        # Compare with expected ratios
        # Allow small tolerance (0.2) for rounding differences
        tolerance = 0.2
        for component, expected_parts in expected_ratio.items():
            actual_parts = actual_ratios[component]
            if abs(actual_parts - expected_parts) > tolerance:
                return False, f"Ratio mismatch for {component}: expected {expected_parts}, got {actual_parts:.1f}"

        return True, "Ratios are correct"

    def calculate_coverage_estimate(self, total_amount: float, coats: int = 2) -> float:
        """
        FUTURE FEATURE: Estimates coverage area in square feet.
        
        Note: This functionality is implemented for future use but not currently
        exposed in the UI. It demonstrates algorithm implementation as part of 
        the capstone project Enhancement Two.
        
        Based on industry standard ~350 sq ft per gallon.
        For paint, density is approximately 1g/ml, so grams and ml are interchangeable.
        
        Args:
            total_amount: Total paint amount in grams (or ml, as 1g ≈ 1ml for paint)
            coats: Number of coats to apply (default 2)
            
        Returns:
            Estimated coverage in square feet
        """
        # Convert grams to gallons (1 gallon = 3785g, assuming paint density ~1g/ml)
        gallons = total_amount / 3785
        
        # Industry standard: ~350-400 sq ft per gallon (using 350 for conservative estimate)
        coverage_per_gallon = 350
        
        # Calculate total coverage accounting for number of coats
        single_coat_coverage = gallons * coverage_per_gallon
        total_coverage = single_coat_coverage / coats
        
        return round(total_coverage, 1)
