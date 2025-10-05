"""
Query functions for the correlation graph.
"""

import json
import networkx as nx
from collections import Counter
from typing import List, Tuple


def load_from_json(nodes_file: str, edges_file: str) -> nx.Graph:
    """
    Load graph from JSON node and edge files.
    
    Args:
        nodes_file: Path to nodes JSON file
        edges_file: Path to edges JSON file
    
    Returns:
        NetworkX graph object
    """
    with open(nodes_file, 'r') as f:
        nodes_data = json.load(f)
    
    with open(edges_file, 'r') as f:
        edges_data = json.load(f)
    
    G = nx.Graph()
    
    # Add nodes with their attributes
    for node in nodes_data:
        node_id = node.get('id')
        if node_id is None:
            continue  # Skip nodes without ID
        attributes = {k: v for k, v in node.items() if k != 'id'}
        G.add_node(node_id, **attributes)
    
    # Add edges with their attributes (skip invalid edges)
    skipped_edges = 0
    for edge in edges_data:
        source = edge.get('source')
        target = edge.get('target')
        
        # Skip edges with None values or missing nodes
        if source is None or target is None:
            skipped_edges += 1
            continue
        
        if source not in G.nodes() or target not in G.nodes():
            skipped_edges += 1
            continue
            
        attributes = {k: v for k, v in edge.items() if k not in ['source', 'target']}
        G.add_edge(source, target, **attributes)
    
    if skipped_edges > 0:
        print(f"Warning: Skipped {skipped_edges} invalid edges")
    
    return G


def top_techniques(G: nx.Graph, n: int = 5) -> List[Tuple[str, int]]:
    """
    Return top N ATT&CK techniques by connection count (degree).
    """
    technique_nodes = [
        (node, G.degree(node)) 
        for node, data in G.nodes(data=True) 
        if data.get('type') == 'technique'
    ]
    technique_nodes.sort(key=lambda x: x[1], reverse=True)
    return technique_nodes[:n]


def top_cves(G: nx.Graph, n: int = 5) -> List[Tuple[str, int]]:
    """
    Return top N CVEs by connection count (degree).
    """
    cve_nodes = [
        (node, G.degree(node)) 
        for node, data in G.nodes(data=True) 
        if data.get('type') == 'cve'
    ]
    cve_nodes.sort(key=lambda x: x[1], reverse=True)
    return cve_nodes[:n]


def top_malware_families(G: nx.Graph, n: int = 5) -> List[Tuple[str, int]]:
    """
    Return top N malware families by connection count.
    """
    malware_nodes = [
        (node, G.degree(node)) 
        for node, data in G.nodes(data=True) 
        if data.get('type') == 'malware_family'
    ]
    malware_nodes.sort(key=lambda x: x[1], reverse=True)
    return malware_nodes[:n]


def top_asns(G: nx.Graph, n: int = 5) -> List[Tuple[str, int]]:
    """
    Return top N ASNs by connection count.
    """
    asn_nodes = [
        (node, G.degree(node)) 
        for node, data in G.nodes(data=True) 
        if data.get('type') == 'asn'
    ]
    asn_nodes.sort(key=lambda x: x[1], reverse=True)
    return asn_nodes[:n]


def graph_stats(G: nx.Graph) -> dict:
    """
    Return basic statistics about the graph.
    """
    node_types = Counter(data.get('type', 'unknown') for _, data in G.nodes(data=True))
    
    return {
        'total_nodes': G.number_of_nodes(),
        'total_edges': G.number_of_edges(),
        'node_types': dict(node_types),
        'density': nx.density(G),
        'connected_components': nx.number_connected_components(G)
    }
