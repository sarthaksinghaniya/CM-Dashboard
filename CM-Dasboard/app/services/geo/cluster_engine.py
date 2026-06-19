from typing import List, Dict, Any
import logging
from sklearn.cluster import DBSCAN
import numpy as np

logger = logging.getLogger(__name__)

class ClusterEngine:
    """
    Groups geo-tagged complaints into clusters to identify hotspots.
    """
    
    def __init__(self, eps_km: float = 2.0, min_samples: int = 3):
        # eps parameter for DBSCAN (in kilometers)
        # Haversine formula requires radians.
        self.kms_per_radian = 6371.0088
        self.eps = eps_km / self.kms_per_radian
        self.min_samples = min_samples

    def analyze_hotspots(self, memory_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes raw FAISS metadata records and computes geographic clusters.
        """
        if not memory_records:
            return []
            
        coords = []
        valid_records = []
        
        # Extract valid geolocated records
        for record in memory_records:
            loc = record.get("location")
            if loc and "lat" in loc and "lon" in loc:
                coords.append([loc["lat"], loc["lon"]])
                valid_records.append(record)
                
        if len(coords) == 0:
            return []
            
        # Convert to radians for Haversine
        coords = np.radians(coords)
        
        # Run DBSCAN
        db = DBSCAN(eps=self.eps, min_samples=self.min_samples, algorithm='ball_tree', metric='haversine')
        labels = db.fit_predict(coords)
        
        # Process clusters
        clusters = {}
        for i, label in enumerate(labels):
            if label == -1:
                # Noise / unclustered
                continue
                
            if label not in clusters:
                clusters[label] = {
                    "cluster_id": int(label),
                    "complaints": [],
                    "lat_sum": 0.0,
                    "lon_sum": 0.0
                }
                
            clusters[label]["complaints"].append(valid_records[i])
            clusters[label]["lat_sum"] += valid_records[i]["location"]["lat"]
            clusters[label]["lon_sum"] += valid_records[i]["location"]["lon"]
            
        # Format output
        results = []
        for label, data in clusters.items():
            count = len(data["complaints"])
            avg_lat = data["lat_sum"] / count
            avg_lon = data["lon_sum"] / count
            
            # Aggregate categories to find top issues
            issue_counts = {}
            for comp in data["complaints"]:
                cats = comp.get("complaint_categories", [])
                for cat in cats:
                    issue_counts[cat] = issue_counts.get(cat, 0) + 1
                    
            # Sort top issues
            top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
            top_issues = [issue[0] for issue in top_issues[:3]]  # Top 3
            
            # Determine region name from the most common area_name in cluster
            areas = [c["location"].get("area_name", "Unknown") for c in data["complaints"]]
            from collections import Counter
            primary_region = Counter(areas).most_common(1)[0][0]
            
            results.append({
                "cluster_id": f"HOTSPOT-{label}",
                "region": primary_region,
                "center_lat": round(avg_lat, 4),
                "center_lon": round(avg_lon, 4),
                "complaint_count": count,
                "top_issues": top_issues,
                "hotspot": True # Since we used min_samples=3, by definition this cluster is a hotspot
            })
            
        return results
