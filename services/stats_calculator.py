"""Statistics calculator for custom baseball metrics."""

from typing import Dict, Any, Tuple
from utils.logger import Logger

logger = Logger.get_logger(__name__)


class StatsCalculator:
    """Calculator for custom baseball statistics like TBR and TBR+."""
    
    @staticmethod
    def calculate_tbr_stats(stats: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate both TBR and TBR+ in one pass.
        
        TBR (Total Base Rate) measures base advancement per plate appearance.
        TBR+ extends TBR by adding runs and RBIs to reward scoring.
        
        TBR Formula: (singles + 2×2B + 3×3B + 4×HR + BB + HBP + 0.75×SB + 0.5×SF + 0.5×SH - 0.5×GIDP - 0.75×CS) / PA
        TBR+ Formula: TBR numerator + 0.75×runs + 0.75×RBIs, then divide by PA
        
        Args:
            stats: Dictionary with player statistics
            
        Returns:
            Tuple of (tbr, tbr_plus), both rounded to 3 decimal places
        """
        try:
            # Extract all stats once
            hits = int(stats.get('hits', 0))
            doubles = int(stats.get('doubles', 0))
            triples = int(stats.get('triples', 0))
            hr = int(stats.get('homeRuns', 0))
            bb = int(stats.get('baseOnBalls', 0))
            hbp = int(stats.get('hitByPitch', 0))
            sb = int(stats.get('stolenBases', 0))
            cs = int(stats.get('caughtStealing', 0))
            sf = int(stats.get('sacFlies', 0))
            sh = int(stats.get('sacBunts', 0))
            gidp = int(stats.get('groundIntoDoublePlay', 0))
            runs = int(stats.get('runs', 0))
            rbis = int(stats.get('rbi', 0))
            pa = int(stats.get('plateAppearances', 0))
            
            # Avoid division by zero
            if pa == 0:
                return 0.0, 0.0
            
            # Calculate singles
            singles = hits - doubles - triples - hr
            
            # Calculate base TBR numerator
            tbr_numerator = (singles + 2*doubles + 3*triples + 4*hr + bb + hbp + 
                           0.75*sb + 0.5*sf + 0.5*sh - 0.5*gidp - 0.75*cs)
            
            # Calculate TBR+ numerator (adds runs and RBIs)
            tbr_plus_numerator = tbr_numerator + 0.75*runs + 0.75*rbis
            
            # Calculate both rates
            tbr = round(tbr_numerator / pa, 3)
            tbr_plus = round(tbr_plus_numerator / pa, 3)
            
            return tbr, tbr_plus
            
        except Exception as e:
            logger.error(f"Error calculating TBR stats: {e}", extra={"stats": stats})
            return 0.0, 0.0
