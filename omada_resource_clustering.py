#!/usr/bin/env python3
"""
K-Means clustering analysis of Omada resource assignments across all identities.
This script performs unsupervised machine learning to identify interesting patterns
in resource assignments and detect outliers.
"""

import os
import sys
import asyncio
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict
import warnings

# Suppress sklearn warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score
    from sklearn.ensemble import IsolationForest
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError as e:
    print(f"Error: Required ML libraries not installed. Please install with:")
    print("pip install scikit-learn pandas numpy matplotlib seaborn")
    sys.exit(1)

# Add the current directory to Python path so we can import from server.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from server import get_all_omada_identities, query_calculated_assignments
except ImportError:
    print("Error: Could not import from server.py. Make sure server.py is in the same directory.")
    sys.exit(1)


class OmadaResourceClusterAnalyzer:
    """
    K-Means clustering analyzer for Omada resource assignments.
    Identifies patterns in resource assignments across all identities.
    """
    
    def __init__(self):
        self.identities_data = []
        self.assignments_data = []
        self.resource_matrix = None
        self.identity_mapping = {}
        self.resource_mapping = {}
        self.clusters = None
        self.outliers = None
        self.scaler = StandardScaler()
        
    async def collect_omada_data(self, max_identities: int = 500) -> Dict[str, Any]:
        """
        Collect all identities and their resource assignments from Omada.
        
        Args:
            max_identities: Maximum number of identities to analyze (for performance)
            
        Returns:
            Dictionary with collection status and statistics
        """
        print("🔍 Collecting Omada identities...")
        
        try:
            # Get all identities with pagination
            identities_result = await get_all_omada_identities(
                top=max_identities,
                select_fields="Id,DISPLAYNAME,FIRSTNAME,LASTNAME",
                include_count=True
            )
            
            identities_data = json.loads(identities_result)
            
            if identities_data.get("status") != "success":
                return {"status": "error", "message": f"Failed to get identities: {identities_data}"}
            
            identities = identities_data["data"]["value"]
            total_identities = len(identities)
            
            print(f"📊 Found {total_identities} identities. Collecting resource assignments...")
            
            # Collect assignments for each identity
            assignment_collection = []
            processed = 0
            
            for identity in identities:
                identity_id = identity.get("Id")
                display_name = identity.get("DISPLAYNAME", "Unknown")
                
                if not identity_id:
                    continue
                
                try:
                    # Get calculated assignments for this identity
                    # Convert identity_id to int and use safer field selection
                    try:
                        # First try with expand
                        assignments_result = await query_calculated_assignments(
                            identity_id=int(identity_id),
                            select_fields="AssignmentKey,AccountName",
                            expand="Identity,Resource,ResourceType",
                            top=100  # Limit results per identity for performance
                        )
                    except Exception as expand_error:
                        if "400" in str(expand_error):
                            # Fallback: try without expand
                            print(f"   Retrying {display_name} without expand...")
                            assignments_result = await query_calculated_assignments(
                                identity_id=int(identity_id),
                                select_fields="AssignmentKey,AccountName",
                                top=100
                            )
                        else:
                            raise expand_error
                    
                    assignments_data = json.loads(assignments_result)
                    
                    if assignments_data.get("status") == "success" and "data" in assignments_data:
                        assignments = assignments_data["data"]["value"]
                        
                        # Extract resource information
                        resources = []
                        for assignment in assignments:
                            # Try multiple ways to get the resource name
                            resource_name = "Unknown"
                            if "Resource" in assignment and isinstance(assignment["Resource"], dict):
                                resource_name = assignment["Resource"].get("DISPLAYNAME") or assignment["Resource"].get("name") or assignment["Resource"].get("Name", "Unknown")
                            elif "ResourceName" in assignment:
                                resource_name = assignment["ResourceName"]
                            
                            account_name = assignment.get("AccountName", "Unknown")
                            assignment_key = assignment.get("AssignmentKey", "Unknown")
                            
                            resources.append({
                                "resource_name": resource_name,
                                "account_name": account_name,
                                "assignment_key": assignment_key
                            })
                        
                        assignment_collection.append({
                            "identity_id": identity_id,
                            "display_name": display_name,
                            "resources": resources,
                            "resource_count": len(resources)
                        })
                    
                    processed += 1
                    if processed % 50 == 0:
                        print(f"   Processed {processed}/{total_identities} identities...")
                        
                except ValueError as e:
                    print(f"   Warning: Invalid identity_id '{identity_id}' for {display_name}: {e}")
                    continue
                except Exception as e:
                    print(f"   Warning: Failed to get assignments for {display_name} (ID: {identity_id}): {e}")
                    
                    # If this is an HTTP 400 error, let's see more details
                    if "400" in str(e) or "Bad" in str(e):
                        print(f"   HTTP 400 Details - Identity ID: {identity_id}, Type: {type(identity_id)}")
                        # Try to parse the assignments_result if it exists
                        try:
                            if 'assignments_result' in locals():
                                error_details = json.loads(assignments_result)
                                print(f"   Error response: {error_details}")
                        except:
                            pass
                    continue
            
            self.identities_data = identities
            self.assignments_data = assignment_collection
            
            return {
                "status": "success",
                "total_identities": total_identities,
                "identities_with_assignments": len(assignment_collection),
                "total_assignments": sum(item["resource_count"] for item in assignment_collection)
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Data collection failed: {str(e)}"}
    
    def prepare_clustering_data(self) -> Dict[str, Any]:
        """
        Prepare data for K-means clustering by creating a resource assignment matrix.
        
        Returns:
            Dictionary with preparation status and statistics
        """
        print("🔧 Preparing data for clustering...")
        
        if not self.assignments_data:
            return {"status": "error", "message": "No assignment data available"}
        
        # Get all unique resources across all identities
        all_resources = set()
        for item in self.assignments_data:
            for resource in item["resources"]:
                all_resources.add(resource["resource_name"])
        
        all_resources = sorted(list(all_resources))
        resource_count = len(all_resources)
        
        print(f"📈 Found {resource_count} unique resources across all identities")
        
        # Create resource mapping
        self.resource_mapping = {resource: idx for idx, resource in enumerate(all_resources)}
        
        # Create identity mapping
        self.identity_mapping = {
            item["identity_id"]: {
                "index": idx,
                "display_name": item["display_name"],
                "resource_count": item["resource_count"]
            }
            for idx, item in enumerate(self.assignments_data)
        }
        
        # Create binary resource assignment matrix
        identity_count = len(self.assignments_data)
        self.resource_matrix = np.zeros((identity_count, resource_count))
        
        for identity_idx, item in enumerate(self.assignments_data):
            for resource in item["resources"]:
                resource_idx = self.resource_mapping.get(resource["resource_name"])
                if resource_idx is not None:
                    self.resource_matrix[identity_idx, resource_idx] = 1
        
        # Add some statistical features
        # Feature 1: Total resource count per identity
        total_resources = np.sum(self.resource_matrix, axis=1).reshape(-1, 1)
        
        # Feature 2: Resource diversity (number of unique resource types)
        resource_diversity = np.sum(self.resource_matrix > 0, axis=1).reshape(-1, 1)
        
        # Combine binary matrix with statistical features
        self.resource_matrix = np.hstack([
            self.resource_matrix,
            total_resources,
            resource_diversity
        ])
        
        return {
            "status": "success",
            "identity_count": identity_count,
            "resource_count": resource_count,
            "matrix_shape": self.resource_matrix.shape,
            "sparsity": 1.0 - (np.count_nonzero(self.resource_matrix) / self.resource_matrix.size)
        }
    
    def perform_clustering(self, n_clusters: int = None, max_clusters: int = 10) -> Dict[str, Any]:
        """
        Perform K-means clustering with optimal cluster selection.
        
        Args:
            n_clusters: Specific number of clusters (if None, will find optimal)
            max_clusters: Maximum number of clusters to try
            
        Returns:
            Dictionary with clustering results and statistics
        """
        print("🎯 Performing K-means clustering...")
        
        if self.resource_matrix is None:
            return {"status": "error", "message": "No prepared data available"}
        
        # Scale the features
        scaled_matrix = self.scaler.fit_transform(self.resource_matrix)
        
        # Find optimal number of clusters if not specified
        if n_clusters is None:
            print("🔍 Finding optimal number of clusters...")
            
            inertias = []
            silhouette_scores = []
            cluster_range = range(2, min(max_clusters + 1, len(self.assignments_data) // 2))
            
            for k in cluster_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(scaled_matrix)
                
                inertias.append(kmeans.inertia_)
                
                if len(set(labels)) > 1:  # Need at least 2 clusters for silhouette score
                    sil_score = silhouette_score(scaled_matrix, labels)
                    silhouette_scores.append(sil_score)
                else:
                    silhouette_scores.append(0)
            
            # Use elbow method and silhouette score to find optimal k
            if silhouette_scores:
                optimal_k = cluster_range[np.argmax(silhouette_scores)]
            else:
                optimal_k = 3  # Default fallback
            
            n_clusters = optimal_k
            print(f"📊 Optimal number of clusters: {n_clusters}")
        
        # Perform final clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(scaled_matrix)
        
        # Calculate clustering metrics
        silhouette_avg = silhouette_score(scaled_matrix, cluster_labels) if len(set(cluster_labels)) > 1 else 0
        
        # Store clustering results
        self.clusters = {
            "labels": cluster_labels,
            "centers": kmeans.cluster_centers_,
            "n_clusters": n_clusters,
            "silhouette_score": silhouette_avg,
            "inertia": kmeans.inertia_
        }
        
        return {
            "status": "success",
            "n_clusters": n_clusters,
            "silhouette_score": silhouette_avg,
            "inertia": kmeans.inertia_
        }
    
    def detect_outliers(self, contamination: float = 0.1) -> Dict[str, Any]:
        """
        Detect outlier identities using Isolation Forest.
        
        Args:
            contamination: Expected proportion of outliers
            
        Returns:
            Dictionary with outlier detection results
        """
        print("🔍 Detecting outliers...")
        
        if self.resource_matrix is None:
            return {"status": "error", "message": "No prepared data available"}
        
        # Scale the features
        scaled_matrix = self.scaler.transform(self.resource_matrix)
        
        # Perform outlier detection
        isolation_forest = IsolationForest(contamination=contamination, random_state=42)
        outlier_labels = isolation_forest.fit_predict(scaled_matrix)
        
        # Get outlier scores
        outlier_scores = isolation_forest.decision_function(scaled_matrix)
        
        # Store outlier results
        outliers_mask = outlier_labels == -1
        self.outliers = {
            "labels": outlier_labels,
            "scores": outlier_scores,
            "outlier_indices": np.where(outliers_mask)[0],
            "outlier_count": np.sum(outliers_mask)
        }
        
        return {
            "status": "success",
            "outlier_count": int(np.sum(outliers_mask)),
            "contamination": contamination
        }
    
    def analyze_clusters(self) -> Dict[str, Any]:
        """
        Analyze clusters to identify interesting patterns and characteristics.
        
        Returns:
            Dictionary with detailed cluster analysis
        """
        print("📈 Analyzing clusters...")
        
        if self.clusters is None or self.resource_matrix is None:
            return {"status": "error", "message": "No clustering results available"}
        
        cluster_labels = self.clusters["labels"]
        n_clusters = self.clusters["n_clusters"]
        
        cluster_analysis = {}
        
        for cluster_id in range(n_clusters):
            cluster_mask = cluster_labels == cluster_id
            cluster_indices = np.where(cluster_mask)[0]
            cluster_size = len(cluster_indices)
            
            # Get identities in this cluster
            cluster_identities = []
            cluster_resources = defaultdict(int)
            total_assignments = 0
            
            for idx in cluster_indices:
                identity_item = self.assignments_data[idx]
                cluster_identities.append({
                    "identity_id": identity_item["identity_id"],
                    "display_name": identity_item["display_name"],
                    "resource_count": identity_item["resource_count"]
                })
                
                # Count resources in this cluster
                for resource in identity_item["resources"]:
                    cluster_resources[resource["resource_name"]] += 1
                    total_assignments += 1
            
            # Find most common resources in this cluster
            common_resources = sorted(cluster_resources.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Calculate cluster statistics
            resource_counts = [identity["resource_count"] for identity in cluster_identities]
            
            cluster_analysis[f"cluster_{cluster_id}"] = {
                "size": cluster_size,
                "percentage": (cluster_size / len(self.assignments_data)) * 100,
                "identities": cluster_identities[:5],  # Show top 5 identities
                "total_identities": cluster_size,
                "common_resources": [
                    {"resource": resource, "count": count, "percentage": (count/cluster_size)*100}
                    for resource, count in common_resources
                ],
                "statistics": {
                    "avg_resource_count": np.mean(resource_counts),
                    "median_resource_count": np.median(resource_counts),
                    "min_resource_count": np.min(resource_counts),
                    "max_resource_count": np.max(resource_counts),
                    "total_assignments": total_assignments
                }
            }
        
        return {
            "status": "success",
            "clusters": cluster_analysis,
            "summary": {
                "total_clusters": n_clusters,
                "silhouette_score": self.clusters["silhouette_score"],
                "total_identities": len(self.assignments_data)
            }
        }
    
    def analyze_outliers(self) -> Dict[str, Any]:
        """
        Analyze detected outliers to understand what makes them unusual.
        
        Returns:
            Dictionary with outlier analysis
        """
        print("🔍 Analyzing outliers...")
        
        if self.outliers is None:
            return {"status": "error", "message": "No outlier detection results available"}
        
        outlier_indices = self.outliers["outlier_indices"]
        outlier_scores = self.outliers["scores"]
        
        if len(outlier_indices) == 0:
            return {"status": "success", "outliers": [], "message": "No outliers detected"}
        
        outlier_analysis = []
        
        for idx in outlier_indices:
            identity_item = self.assignments_data[idx]
            outlier_score = outlier_scores[idx]
            
            # Get outlier's resource pattern
            outlier_resources = [resource["resource_name"] for resource in identity_item["resources"]]
            
            outlier_analysis.append({
                "identity_id": identity_item["identity_id"],
                "display_name": identity_item["display_name"],
                "resource_count": identity_item["resource_count"],
                "outlier_score": float(outlier_score),
                "resources": outlier_resources[:10],  # Show top 10 resources
                "total_resources": len(outlier_resources)
            })
        
        # Sort by outlier score (most anomalous first)
        outlier_analysis.sort(key=lambda x: x["outlier_score"])
        
        return {
            "status": "success",
            "outlier_count": len(outlier_analysis),
            "outliers": outlier_analysis,
            "summary": {
                "most_anomalous": outlier_analysis[0] if outlier_analysis else None,
                "avg_outlier_score": float(np.mean(outlier_scores[outlier_indices])),
                "outlier_resource_stats": {
                    "avg_resource_count": float(np.mean([o["resource_count"] for o in outlier_analysis])),
                    "max_resource_count": max([o["resource_count"] for o in outlier_analysis]) if outlier_analysis else 0
                }
            }
        }
    
    async def run_full_analysis(self, max_identities: int = 500, n_clusters: int = None) -> Dict[str, Any]:
        """
        Run the complete clustering analysis pipeline.
        
        Args:
            max_identities: Maximum number of identities to analyze
            n_clusters: Number of clusters (if None, will find optimal)
            
        Returns:
            Complete analysis results
        """
        print("🚀 Starting Omada Resource Clustering Analysis")
        print("=" * 60)
        
        results = {
            "analysis_timestamp": pd.Timestamp.now().isoformat(),
            "parameters": {
                "max_identities": max_identities,
                "n_clusters": n_clusters
            }
        }
        
        # Step 1: Collect data
        collection_result = await self.collect_omada_data(max_identities)
        results["data_collection"] = collection_result
        
        if collection_result["status"] != "success":
            return results
        
        # Step 2: Prepare data
        preparation_result = self.prepare_clustering_data()
        results["data_preparation"] = preparation_result
        
        if preparation_result["status"] != "success":
            return results
        
        # Step 3: Perform clustering
        clustering_result = self.perform_clustering(n_clusters)
        results["clustering"] = clustering_result
        
        if clustering_result["status"] != "success":
            return results
        
        # Step 4: Detect outliers
        outlier_result = self.detect_outliers()
        results["outlier_detection"] = outlier_result
        
        # Step 5: Analyze clusters
        cluster_analysis_result = self.analyze_clusters()
        results["cluster_analysis"] = cluster_analysis_result
        
        # Step 6: Analyze outliers
        outlier_analysis_result = self.analyze_outliers()
        results["outlier_analysis"] = outlier_analysis_result
        
        print("\n✅ Analysis complete!")
        return results


def print_analysis_summary(results: Dict[str, Any]) -> None:
    """Print a formatted summary of the analysis results."""
    
    print("\n" + "="*80)
    print("📊 OMADA RESOURCE CLUSTERING ANALYSIS SUMMARY")
    print("="*80)
    
    # Data collection summary
    if "data_collection" in results and results["data_collection"]["status"] == "success":
        dc = results["data_collection"]
        print(f"\n📈 Data Collection:")
        print(f"  • Total identities: {dc['total_identities']}")
        print(f"  • Identities with assignments: {dc['identities_with_assignments']}")
        print(f"  • Total assignments: {dc['total_assignments']}")
    
    # Clustering summary
    if "cluster_analysis" in results and results["cluster_analysis"]["status"] == "success":
        ca = results["cluster_analysis"]
        summary = ca["summary"]
        
        print(f"\n🎯 Clustering Results:")
        print(f"  • Number of clusters: {summary['total_clusters']}")
        print(f"  • Silhouette score: {summary['silhouette_score']:.3f}")
        print(f"  • Total identities analyzed: {summary['total_identities']}")
        
        print(f"\n🔍 Most Interesting Clusters:")
        clusters = ca["clusters"]
        
        # Sort clusters by size for interest
        cluster_items = [(k, v) for k, v in clusters.items()]
        cluster_items.sort(key=lambda x: x[1]["size"], reverse=True)
        
        for i, (cluster_name, cluster_data) in enumerate(cluster_items[:3]):
            print(f"\n  Cluster {i+1} ({cluster_data['size']} identities, {cluster_data['percentage']:.1f}%):")
            print(f"    Average resources per identity: {cluster_data['statistics']['avg_resource_count']:.1f}")
            
            print(f"    Top resources in this cluster:")
            for j, resource_info in enumerate(cluster_data['common_resources'][:5]):
                print(f"      {j+1}. {resource_info['resource']} ({resource_info['count']} identities, {resource_info['percentage']:.1f}%)")
            
            if cluster_data['identities']:
                print(f"    Example identities:")
                for identity in cluster_data['identities'][:3]:
                    print(f"      • {identity['display_name']} ({identity['resource_count']} resources)")
    
    # Outliers summary
    if "outlier_analysis" in results and results["outlier_analysis"]["status"] == "success":
        oa = results["outlier_analysis"]
        
        print(f"\n🚨 Outlier Detection:")
        print(f"  • Outliers found: {oa['outlier_count']}")
        
        if oa["outliers"]:
            print(f"  • Most anomalous identity: {oa['summary']['most_anomalous']['display_name']}")
            print(f"    - Resource count: {oa['summary']['most_anomalous']['resource_count']}")
            print(f"    - Outlier score: {oa['summary']['most_anomalous']['outlier_score']:.3f}")
            
            print(f"\n  Top 5 Outliers:")
            for i, outlier in enumerate(oa["outliers"][:5]):
                print(f"    {i+1}. {outlier['display_name']} ({outlier['resource_count']} resources, score: {outlier['outlier_score']:.3f})")


async def main():
    """Main execution function."""
    
    try:
        # Create analyzer
        analyzer = OmadaResourceClusterAnalyzer()
        
        # Run full analysis
        results = await analyzer.run_full_analysis(
            max_identities=500,  # Adjust based on your system size
            n_clusters=None      # Auto-detect optimal clusters
        )
        
        # Print summary
        print_analysis_summary(results)
        
        # Save detailed results
        output_file = "omada_clustering_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())