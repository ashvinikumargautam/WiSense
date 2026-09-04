# app/api/analytics.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text  # Using raw SQL to avoid model import errors
from app.database.database import get_session

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/timeseries")
async def get_movement_timeseries(db: AsyncSession = Depends(get_session)):
    """Fetch the last 50 detections to plot on the frontend chart."""
    try:
        # Raw SQL query - adjust column names if yours are slightly different
        query = text("""
            SELECT created_at, activity, confidence 
            FROM detections 
            ORDER BY created_at DESC 
            LIMIT 50
        """)
        result = await db.execute(query)
        rows = result.fetchall()
        
        # Reverse the list so oldest is first (for left-to-right chart drawing)
        rows_list = list(rows)
        rows_list.reverse()
        
        data = []
        for row in rows_list:
            # Unpack the row (created_at, activity, confidence)
            created_at_val = row[0]
            activity_val = row[1]
            confidence_val = row[2]
            
            time_str = created_at_val.strftime("%H:%M:%S") if created_at_val else "00:00:00"
            
            if confidence_val is not None:
                conf = float(confidence_val)
            else:
                # Fallback if no confidence column
                conf = 1.0 if activity_val and activity_val != "NO_MOVEMENT" else 0.0
                
            data.append({
                "time": time_str,
                "confidence": conf
            })
            
        return data
        
    except Exception as e:
        # If it fails (e.g., column name is slightly different), print the exact error
        print(f"Analytics error: {e}")
        return []