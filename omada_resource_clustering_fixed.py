#!/usr/bin/env python3
"""
K-Means clustering analysis of Omada resource assignments across all identities.
FIXED VERSION - Properly displays identity names and resource details.
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
    FIXED VERSION - Properly extracts and displays identity and resource information.
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
        FIXED: Proper identity name extraction and counting.
        """
        print("🔍 Collecting Omada identities...")
        
        try:
            # Get all identities with pagination - include email address
            identities_result = await get_all_omada_identities(
                top=max_identities,
                select_fields="Id,DISPLAYNAME,FIRSTNAME,LASTNAME,EMAIL",
                include_count=True
            )
            
            identities_data = json.loads(identities_result)
            print(f"🔍 Raw identities response status: {identities_data.get('status')}")
            
            if identities_data.get("status") != "success":
                return {"status": "error", "message": f"Failed to get identities: {identities_data}"}
            
            identities = identities_data["data"]["value"]
            actual_identity_count = len(identities)
            
            print(f"📊 Found {actual_identity_count} actual identities")
            if identities:
                print(f"   Sample identity: {identities[0]}")
            
            # Collect assignments for each identity
            assignment_collection = []
            processed = 0
            successful_collections = 0
            
            for identity in identities:
                identity_id = identity.get("Id")
                
                # FIX: Better name extraction with fallback
                firstname = identity.get("FIRSTNAME", "")
                lastname = identity.get("LASTNAME", "")
                email = identity.get("EMAIL", "")
                
                display_name = (
                    identity.get("DISPLAYNAME") or 
                    f"{firstname} {lastname}".strip() or
                    email or
                    f"Identity_{identity_id}"
                )
                
                if not identity_id:
                    print(f"   Skipping identity with no ID: {identity}")
                    continue
                
                try:
                    print(f"   Processing: {display_name} (ID: {identity_id})")
                    
                    # Get calculated assignments - simplified approach
                    assignments_result = await query_calculated_assignments(
                        identity_id=int(identity_id),
                        select_fields="AssignmentKey,AccountName",
                        expand="Resource",  # Only expand Resource, not all
                        top=50  # Reasonable limit per identity
                    )
                    
                    assignments_data = json.loads(assignments_result)
                    
                    if assignments_data.get("status") == "success" and "data" in assignments_data:
                        assignments = assignments_data["data"]["value"]
                        
                        # FIX: Better resource extraction
                        resources = []
                        for assignment in assignments:
                            # Multiple ways to get resource name
                            resource_name = "Unknown_Resource"
                            
                            # Try expanded Resource object first
                            if "Resource" in assignment and isinstance(assignment["Resource"], dict):
                                resource_obj = assignment["Resource"]
                                resource_name = (
                                    resource_obj.get("DISPLAYNAME") or
                                    resource_obj.get("Name") or
                                    resource_obj.get("name") or
                                    f"Resource_{resource_obj.get('Id', 'NoId')}"
                                )
                            
                            # Fallback to assignment key or account name
                            if resource_name == "Unknown_Resource":
                                resource_name = (
                                    assignment.get("AssignmentKey") or
                                    f"Account_{assignment.get('AccountName', 'Unknown')}"
                                )
                            
                            account_name = assignment.get("AccountName", "No_Account")
                            
                            resources.append({
                                "resource_name": resource_name,
                                "account_name": account_name,
                                "assignment_key": assignment.get("AssignmentKey", "No_Key")
                            })
                        
                        if resources:  # Only add if we found resources
                            assignment_collection.append({
                                "identity_id": str(identity_id),
                                "display_name": display_name,
                                "firstname": firstname,
                                "lastname": lastname,
                                "email": email,
                                "resources": resources,
                                "resource_count": len(resources)
                            })
                            successful_collections += 1
                            
                            print(f"     Found {len(resources)} resources")
                            if resources:
                                print(f"     Sample resource: {resources[0]['resource_name']}")
                    else:
                        print(f"     No assignments found for {display_name}")
                    
                    processed += 1
                    if processed % 10 == 0:
                        print(f"   Processed {processed}/{actual_identity_count} identities, {successful_collections} with resources...")
                        
                except ValueError as e:
                    print(f"   ERROR: Invalid identity_id '{identity_id}' for {display_name}: {e}")
                    continue
                except Exception as e:
                    print(f"   ERROR: Failed to get assignments for {display_name} (ID: {identity_id}): {str(e)[:200]}")
                    continue
            
            self.identities_data = identities
            self.assignments_data = assignment_collection
            
            print(f"\n✅ Collection Summary:")
            print(f"   Total identities in system: {actual_identity_count}")
            print(f"   Identities with resource assignments: {len(assignment_collection)}")
            print(f"   Total resource assignments: {sum(item['resource_count'] for item in assignment_collection)}")
            
            return {
                "status": "success",
                "total_identities_in_system": actual_identity_count,
                "identities_with_assignments": len(assignment_collection),
                "total_assignments": sum(item["resource_count"] for item in assignment_collection)
            }
            
        except Exception as e:
            print(f"❌ Data collection failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": f"Data collection failed: {str(e)}"}
    
    def prepare_clustering_data(self) -> Dict[str, Any]:
        """
        Prepare data for K-means clustering by creating a resource assignment matrix.
        """
        print("\n🔧 Preparing data for clustering...")
        
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
        print(f"   Sample resources: {all_resources[:5]}")
        
        # Create resource mapping
        self.resource_mapping = {resource: idx for idx, resource in enumerate(all_resources)}
        
        # Create identity mapping with PROPER names including email
        self.identity_mapping = {}
        for idx, item in enumerate(self.assignments_data):
            self.identity_mapping[item["identity_id"]] = {
                "index": idx,
                "display_name": item["display_name"],  # FIX: Use extracted display name
                "firstname": item.get("firstname", ""),
                "lastname": item.get("lastname", ""),
                "email": item.get("email", ""),
                "resource_count": item["resource_count"]
            }
        
        # Create binary resource assignment matrix
        identity_count = len(self.assignments_data)
        self.resource_matrix = np.zeros((identity_count, resource_count))
        
        for identity_idx, item in enumerate(self.assignments_data):
            for resource in item["resources"]:
                resource_idx = self.resource_mapping.get(resource["resource_name"])
                if resource_idx is not None:
                    self.resource_matrix[identity_idx, resource_idx] = 1
        
        # Add statistical features
        total_resources = np.sum(self.resource_matrix, axis=1).reshape(-1, 1)
        resource_diversity = np.sum(self.resource_matrix > 0, axis=1).reshape(-1, 1)
        
        self.resource_matrix = np.hstack([
            self.resource_matrix,
            total_resources,
            resource_diversity
        ])
        
        return {
            "status": "success",
            "identity_count": identity_count,
            "resource_count": resource_count,
            "matrix_shape": self.resource_matrix.shape
        }
    
    def perform_clustering(self, n_clusters: int = None, max_clusters: int = 8) -> Dict[str, Any]:
        """
        Perform K-means clustering with optimal cluster selection.
        """
        print("\n🎯 Performing K-means clustering...")
        
        if self.resource_matrix is None:
            return {"status": "error", "message": "No prepared data available"}
        
        # Scale the features
        scaled_matrix = self.scaler.fit_transform(self.resource_matrix)
        
        # Find optimal number of clusters if not specified
        if n_clusters is None:
            print("🔍 Finding optimal number of clusters...")
            
            silhouette_scores = []
            cluster_range = range(2, min(max_clusters + 1, len(self.assignments_data) // 3))
            
            for k in cluster_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(scaled_matrix)
                
                if len(set(labels)) > 1:
                    sil_score = silhouette_score(scaled_matrix, labels)
                    silhouette_scores.append(sil_score)
                    print(f"   k={k}: silhouette_score={sil_score:.3f}")
                else:
                    silhouette_scores.append(0)
            
            if silhouette_scores:
                optimal_k = cluster_range[np.argmax(silhouette_scores)]
            else:
                optimal_k = 3
            
            n_clusters = optimal_k
            print(f"📊 Optimal number of clusters: {n_clusters}")
        
        # Perform final clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(scaled_matrix)
        
        silhouette_avg = silhouette_score(scaled_matrix, cluster_labels) if len(set(cluster_labels)) > 1 else 0
        
        self.clusters = {
            "labels": cluster_labels,
            "centers": kmeans.cluster_centers_,
            "n_clusters": n_clusters,
            "silhouette_score": silhouette_avg
        }
        
        return {
            "status": "success",
            "n_clusters": n_clusters,
            "silhouette_score": silhouette_avg
        }
    
    def detect_outliers(self, contamination: float = 0.1) -> Dict[str, Any]:
        """
        Detect outlier identities using Isolation Forest.
        """
        print("\n🔍 Detecting outliers...")
        
        if self.resource_matrix is None:
            return {"status": "error", "message": "No prepared data available"}
        
        scaled_matrix = self.scaler.transform(self.resource_matrix)
        
        isolation_forest = IsolationForest(contamination=contamination, random_state=42)
        outlier_labels = isolation_forest.fit_predict(scaled_matrix)
        outlier_scores = isolation_forest.decision_function(scaled_matrix)
        
        outliers_mask = outlier_labels == -1
        self.outliers = {
            "labels": outlier_labels,
            "scores": outlier_scores,
            "outlier_indices": np.where(outliers_mask)[0],
            "outlier_count": np.sum(outliers_mask)
        }
        
        return {
            "status": "success",
            "outlier_count": int(np.sum(outliers_mask))
        }
    
    def analyze_clusters(self) -> Dict[str, Any]:
        """
        Analyze clusters with PROPER identity names and resource details.
        """
        print("\n📈 Analyzing clusters...")
        
        if self.clusters is None:
            return {"status": "error", "message": "No clustering results available"}
        
        cluster_labels = self.clusters["labels"]
        n_clusters = self.clusters["n_clusters"]
        
        cluster_analysis = {}
        
        for cluster_id in range(n_clusters):
            cluster_mask = cluster_labels == cluster_id
            cluster_indices = np.where(cluster_mask)[0]
            cluster_size = len(cluster_indices)
            
            # Get identities in this cluster with PROPER names and email
            cluster_identities = []
            cluster_resources = defaultdict(int)
            all_cluster_resources = []  # Track all resources for detailed summary
            
            for idx in cluster_indices:
                identity_item = self.assignments_data[idx]
                cluster_identities.append({
                    "identity_id": identity_item["identity_id"],
                    "display_name": identity_item["display_name"],  # FIX: Real names
                    "firstname": identity_item.get("firstname", ""),
                    "lastname": identity_item.get("lastname", ""),
                    "email": identity_item.get("email", ""),
                    "resource_count": identity_item["resource_count"]
                })
                
                # Count resources and track all for summary
                for resource in identity_item["resources"]:
                    resource_name = resource["resource_name"]
                    cluster_resources[resource_name] += 1
                    all_cluster_resources.append(resource_name)
            
            # Sort identities by resource count (most privileged first)
            cluster_identities.sort(key=lambda x: x["resource_count"], reverse=True)
            
            # Get top resources
            common_resources = sorted(cluster_resources.items(), key=lambda x: x[1], reverse=True)[:10]
            
            cluster_analysis[f"cluster_{cluster_id}"] = {
                "size": cluster_size,
                "percentage": (cluster_size / len(self.assignments_data)) * 100,
                "identities": cluster_identities,  # Show ALL identities with email
                "common_resources": [
                    {"resource": resource, "identity_count": count, "percentage": (count/cluster_size)*100}
                    for resource, count in common_resources
                ],
                "all_unique_resources": sorted(list(set(all_cluster_resources))),  # All resources in cluster
                "total_unique_resources": len(set(all_cluster_resources)),
                "resource_stats": {
                    "avg_resources_per_identity": np.mean([i["resource_count"] for i in cluster_identities]),
                    "max_resources": max([i["resource_count"] for i in cluster_identities]) if cluster_identities else 0,
                    "min_resources": min([i["resource_count"] for i in cluster_identities]) if cluster_identities else 0,
                    "total_resource_assignments": len(all_cluster_resources)
                }
            }
        
        return {
            "status": "success",
            "clusters": cluster_analysis
        }
    
    def analyze_outliers(self) -> Dict[str, Any]:
        """
        Analyze outliers with PROPER identity names.
        """
        print("\n🔍 Analyzing outliers...")
        
        if self.outliers is None:
            return {"status": "error", "message": "No outlier results available"}
        
        outlier_indices = self.outliers["outlier_indices"]
        outlier_scores = self.outliers["scores"]
        
        if len(outlier_indices) == 0:
            return {"status": "success", "outliers": []}
        
        outlier_analysis = []
        
        for idx in outlier_indices:
            identity_item = self.assignments_data[idx]
            outlier_score = outlier_scores[idx]
            
            outlier_analysis.append({
                "identity_id": identity_item["identity_id"],
                "display_name": identity_item["display_name"],  # FIX: Real names
                "firstname": identity_item.get("firstname", ""),
                "lastname": identity_item.get("lastname", ""),
                "resource_count": identity_item["resource_count"],
                "outlier_score": float(outlier_score),
                "resources": [r["resource_name"] for r in identity_item["resources"][:10]]
            })
        
        # Sort by outlier score (most anomalous first)
        outlier_analysis.sort(key=lambda x: x["outlier_score"])
        
        return {
            "status": "success",
            "outlier_count": len(outlier_analysis),
            "outliers": outlier_analysis
        }
    
    async def run_full_analysis(self, max_identities: int = 500) -> Dict[str, Any]:
        """
        Run the complete analysis with proper data extraction.
        """
        print("🚀 Starting FIXED Omada Resource Clustering Analysis")
        print("=" * 70)
        
        results = {}
        
        # Collect data
        collection_result = await self.collect_omada_data(max_identities)
        results["data_collection"] = collection_result
        if collection_result["status"] != "success":
            return results
        
        # Prepare data
        prep_result = self.prepare_clustering_data()
        results["data_preparation"] = prep_result
        if prep_result["status"] != "success":
            return results
        
        # Clustering
        cluster_result = self.perform_clustering()
        results["clustering"] = cluster_result
        if cluster_result["status"] != "success":
            return results
        
        # Outliers
        outlier_result = self.detect_outliers()
        results["outlier_detection"] = outlier_result
        
        # Analysis
        cluster_analysis = self.analyze_clusters()
        results["cluster_analysis"] = cluster_analysis
        
        outlier_analysis = self.analyze_outliers()
        results["outlier_analysis"] = outlier_analysis
        
        return results


def print_detailed_summary(results: Dict[str, Any]) -> None:
    """Print a MUCH MORE detailed and useful summary."""
    
    print("\n" + "="*90)
    print("📊 DETAILED OMADA RESOURCE CLUSTERING ANALYSIS")
    print("="*90)
    
    # Data summary
    if "data_collection" in results:
        dc = results["data_collection"]
        print(f"\n📈 DATA COLLECTION:")
        print(f"   • Total identities in Omada system: {dc.get('total_identities_in_system', 'Unknown')}")
        print(f"   • Identities with resource assignments: {dc.get('identities_with_assignments', 'Unknown')}")
        print(f"   • Total resource assignments found: {dc.get('total_assignments', 'Unknown')}")
    
    # Detailed cluster analysis
    if "cluster_analysis" in results and results["cluster_analysis"]["status"] == "success":
        clusters = results["cluster_analysis"]["clusters"]
        
        print(f"\n🎯 CLUSTER ANALYSIS:")
        print(f"   Found {len(clusters)} distinct user groups")
        
        for cluster_name, cluster_data in clusters.items():
            cluster_num = cluster_name.split('_')[1]
            print(f"\n   📋 CLUSTER {cluster_num} - {cluster_data['size']} identities ({cluster_data['percentage']:.1f}%)")
            print(f"      Average resources per user: {cluster_data['resource_stats']['avg_resources_per_identity']:.1f}")
            print(f"      Resource range: {cluster_data['resource_stats']['min_resources']} - {cluster_data['resource_stats']['max_resources']}")
            
            print(f"      🔑 TOP RESOURCES IN THIS GROUP:")
            for i, resource_info in enumerate(cluster_data['common_resources'][:5]):
                print(f"         {i+1}. {resource_info['resource']} - {resource_info['identity_count']} users ({resource_info['percentage']:.1f}%)")
            
            print(f"      👥 SAMPLE IDENTITIES:")
            for i, identity in enumerate(cluster_data['identities'][:5]):
                name = identity['display_name']
                if name and name != "Unknown":
                    print(f"         {i+1}. {name} - {identity['resource_count']} resources")
                else:
                    firstname = identity.get('firstname', '')
                    lastname = identity.get('lastname', '')
                    full_name = f"{firstname} {lastname}".strip() or f"ID_{identity['identity_id']}"
                    print(f"         {i+1}. {full_name} - {identity['resource_count']} resources")
    
    # Detailed outlier analysis
    if "outlier_analysis" in results and results["outlier_analysis"]["status"] == "success":
        outliers = results["outlier_analysis"]["outliers"]
        
        print(f"\n🚨 OUTLIER ANALYSIS:")
        print(f"   Found {len(outliers)} unusual identities")
        
        if outliers:
            print(f"   🔍 TOP OUTLIERS (most unusual access patterns):")
            for i, outlier in enumerate(outliers[:10]):
                name = outlier['display_name']
                if not name or name == "Unknown":
                    firstname = outlier.get('firstname', '')
                    lastname = outlier.get('lastname', '')
                    name = f"{firstname} {lastname}".strip() or f"ID_{outlier['identity_id']}"
                
                print(f"      {i+1}. {name}")
                print(f"         Resources: {outlier['resource_count']}")
                print(f"         Anomaly Score: {outlier['outlier_score']:.3f}")
                if outlier['resources']:
                    print(f"         Sample Resources: {', '.join(outlier['resources'][:3])}")
                print()


async def main():
    """Main execution with better error handling."""
    
    try:
        analyzer = OmadaResourceClusterAnalyzer()
        
        # Run analysis with reasonable limits
        results = await analyzer.run_full_analysis(max_identities=400)
        
        # Print detailed summary
        print_detailed_summary(results)
        
        # Save results
        output_file = "omada_clustering_detailed_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())