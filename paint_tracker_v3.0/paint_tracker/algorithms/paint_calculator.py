"""
Paint mixing calculator - handles ratio calculations for interior/exterior jobs.
Uses industry-standard ratios: 3:1:3 for interior, 3:1:1 for exterior.
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
            # Interior ratio 3:1:3 means for every 3 parts paint, 1 part catalyst, 3 parts additive
            catalyst = paint_amount / 3
            additive = paint_amount  # Same as paint (3:3)
            
            components = {
                'paint': round(paint_amount, 1),
                'catalyst': round(catalyst, 1),
                'additive': round(additive, 1)
            }
        else:  # exterior
            # Exterior ratio 3:1:1 means for every 3 parts paint, 1 part catalyst, 1 part reducer
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
