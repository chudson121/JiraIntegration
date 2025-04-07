#!/usr/bin/env python3
"""
Terraform to AWS Diagram Generator

This script analyzes Terraform files (.tf) in a specified directory,
extracts AWS resource definitions, and generates architecture diagrams.

pip install python-hcl2 graphviz
python terraform_diagram_generator.py /path/to/terraform/files -o my_diagram

C:\Program Files\Graphviz
python tf2diagram.py "E:\SourceCode\CHHJIT\chhj-terraform\apps-infra" -o my_diagram.jpeg
"""
#!/usr/bin/env python3
"""
Enhanced Terraform to AWS Diagram Generator

This script analyzes Terraform files (.tf) in a specified directory,
extracts AWS resource definitions, and generates architecture diagrams
with proper AWS-style grouping and relationships.

Dependencies:
pip install python-hcl2 graphviz

Usage:
python tf2diagram.py /path/to/terraform/files -o my_diagram.png
"""

import os
import re
import json
import argparse
from typing import Dict, List, Any, Set, Tuple
import hcl2
import graphviz as gv

# Define AWS resource types with improved visualization settings
AWS_RESOURCE_TYPES = {
    # Network
    "aws_vpc": {"shape": "box", "label": "VPC", "color": "#F9DFCB", "group": "network", "container": True},
    "aws_subnet": {"shape": "box", "label": "Subnet", "color": "#D8E4F1", "group": "network", "parent": "vpc"},
    "aws_security_group": {"shape": "box", "label": "Security Group", "color": "#FFEACC", "group": "network"},
    "aws_internet_gateway": {"shape": "diamond", "label": "IGW", "color": "#D8E4F1", "group": "network"},
    "aws_route_table": {"shape": "box", "label": "Route Table", "color": "#D8E4F1", "group": "network"},
    "aws_nat_gateway": {"shape": "diamond", "label": "NAT Gateway", "color": "#D8E4F1", "group": "network"},
    
    # Compute
    "aws_instance": {"shape": "box", "label": "EC2", "color": "#FCE2D7", "group": "compute"},
    "aws_launch_template": {"shape": "box", "label": "Launch Template", "color": "#FCE2D7", "group": "compute"},
    "aws_autoscaling_group": {"shape": "box", "label": "Auto Scaling", "color": "#F8CECC", "group": "compute"},
    
    # Load Balancing
    "aws_lb": {"shape": "box", "label": "Load Balancer", "color": "#D0E0FC", "group": "loadbalancing"},
    "aws_lb_target_group": {"shape": "box", "label": "Target Group", "color": "#D0E0FC", "group": "loadbalancing"},
    "aws_lb_listener": {"shape": "ellipse", "label": "Listener", "color": "#D0E0FC", "group": "loadbalancing"},
    
    # Containers
    "aws_ecs_cluster": {"shape": "box", "label": "ECS Cluster", "color": "#FFE6CC", "group": "containers", "container": True},
    "aws_ecs_service": {"shape": "box", "label": "ECS Service", "color": "#FFD9B3", "group": "containers", "parent": "ecs_cluster"},
    "aws_ecs_task_definition": {"shape": "box", "label": "ECS Task", "color": "#FFCC99", "group": "containers"},
    "aws_ecr_repository": {"shape": "cylinder", "label": "ECR Repo", "color": "#D9EAD3", "group": "containers"},
    
    # Storage
    "aws_s3_bucket": {"shape": "cylinder", "label": "S3", "color": "#E6F5D0", "group": "storage"},
    "aws_rds_cluster": {"shape": "cylinder", "label": "RDS Cluster", "color": "#DAE8FC", "group": "database", "container": True},
    "aws_rds_instance": {"shape": "cylinder", "label": "RDS Instance", "color": "#DAE8FC", "group": "database"},
    "aws_dynamodb_table": {"shape": "cylinder", "label": "DynamoDB", "color": "#E1D5E7", "group": "database"},
    
    # DNS
    "aws_route53_record": {"shape": "ellipse", "label": "Route53", "color": "#E1D5E7", "group": "network"},
    "aws_cloudfront_distribution": {"shape": "ellipse", "label": "CloudFront", "color": "#D0E0E3", "group": "network"},
    
    # Serverless
    "aws_lambda_function": {"shape": "box", "label": "Lambda", "color": "#F5F5F5", "group": "serverless"},
    "aws_api_gateway_rest_api": {"shape": "box", "label": "API Gateway", "color": "#FFE6CC", "group": "serverless"},
    
    # Security
    "aws_iam_role": {"shape": "box", "label": "IAM Role", "color": "#FFF2CC", "group": "security"},
    "aws_iam_policy": {"shape": "note", "label": "IAM Policy", "color": "#FFF2CC", "group": "security"},
    "aws_kms_key": {"shape": "box", "label": "KMS Key", "color": "#D5E8D4", "group": "security"},
    "aws_secretsmanager_secret": {"shape": "box", "label": "Secrets", "color": "#FFF2CC", "group": "security"},
    
    # Monitoring
    "aws_cloudwatch_log_group": {"shape": "box", "label": "CloudWatch Logs", "color": "#E1D5E7", "group": "monitoring"},
    "aws_cloudwatch_alarm": {"shape": "box", "label": "CloudWatch Alarm", "color": "#E1D5E7", "group": "monitoring"},
}

def parse_terraform_files(directory: str) -> Dict[str, Any]:
    """
    Parse all Terraform (.tf) files in the specified directory and return a dictionary
    of the resources defined.
    
    Args:
        directory: Path to directory containing Terraform files
        
    Returns:
        Dictionary of parsed Terraform resources
    """
    all_resources = {}
    
    # Walk through all files in directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.tf'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        try:
                            # Parse HCL content
                            content = hcl2.load(f)
                            
                            # Extract resources
                            if 'resource' in content:
                                resources = content['resource']
                                # Handle resource structure which can be a list of dictionaries
                                for resource_block in resources:
                                    for resource_type, instances in resource_block.items():
                                        # Instances can be a list in some HCL parsers
                                        if isinstance(instances, list):
                                            for instance in instances:
                                                for resource_name, resource_config in instance.items():
                                                    # Create a unique identifier for the resource
                                                    resource_id = f"{resource_type}.{resource_name}"
                                                    all_resources[resource_id] = {
                                                        'type': resource_type,
                                                        'name': resource_name,
                                                        'config': resource_config,
                                                        'file': file_path
                                                    }
                                        # Or a dictionary in others
                                        elif isinstance(instances, dict):
                                            for resource_name, resource_config in instances.items():
                                                resource_id = f"{resource_type}.{resource_name}"
                                                all_resources[resource_id] = {
                                                    'type': resource_type,
                                                    'name': resource_name,
                                                    'config': resource_config,
                                                    'file': file_path
                                                }
                        except Exception as e:
                            print(f"Error parsing {file_path}: {str(e)}")
                except Exception as e:
                    print(f"Error opening {file_path}: {e}")
    
    return all_resources

def extract_references_from_string(text: str) -> List[str]:
    """
    Extract resource references from a string using regex patterns.
    
    Args:
        text: String to search for references
        
    Returns:
        List of resource references found
    """
    references = []
    
    # Regular expressions to find resource references in HCL
    ref_patterns = [
        r'(\${)?\s*([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)(?:\.([a-zA-Z0-9_-]+))?\s*}?',  # ${aws_vpc.main.id}
        r'([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)(?:\.([a-zA-Z0-9_-]+))?'                 # aws_vpc.main.id
    ]
    
    for pattern in ref_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            # Extract referenced resource type and name
            if match.group(1) == '${' or match.group(1) is None:
                # Group arrangement depends on which pattern matched
                if len(match.groups()) == 3:
                    ref_type, ref_name = match.group(2), match.group(3)
                elif len(match.groups()) == 4:
                    ref_type, ref_name = match.group(2), match.group(3)
                else:
                    continue
                
                # Create reference ID
                ref_id = f"{ref_type}.{ref_name}"
                references.append(ref_id)
    
    return references

def extract_relationships(resources: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """
    Extract relationships between resources based on references in their configuration.
    
    Args:
        resources: Dictionary of parsed Terraform resources
        
    Returns:
        List of tuples (source_id, target_id, relationship_type)
    """
    relationships = []
    containment_relationships = []
    
    # First pass: extract direct references from config
    for resource_id, resource in resources.items():
        # Convert config to a string for regex search
        try:
            config_str = json.dumps(resource['config'])
        except TypeError:
            # Handle case where config might not be JSON serializable
            config_str = str(resource['config'])
        
        # Find all references to other resources
        references = extract_references_from_string(config_str)
        
        for ref_id in references:
            # Skip self-references and check if referenced resource exists
            if ref_id != resource_id and ref_id in resources:
                relationships.append((resource_id, ref_id, "references"))
    
    # Second pass: infer logical containment relationships based on AWS architecture
    for resource_id, resource in resources.items():
        resource_type = resource['type']
        
        # Handle special containment cases
        if resource_type == 'aws_subnet':
            # Find the VPC this subnet belongs to from its config
            if 'vpc_id' in resource['config']:
                vpc_ref = resource['config']['vpc_id']
                for vpc_id, vpc in resources.items():
                    if vpc['type'] == 'aws_vpc' and extract_references_from_string(str(vpc_ref)):
                        containment_relationships.append((vpc_id, resource_id, "contains"))
                        break
        
        elif resource_type == 'aws_lb':
            # Load balancers are logically in subnets/VPC
            if 'subnets' in resource['config']:
                subnet_refs = resource['config']['subnets']
                subnet_refs_str = str(subnet_refs)
                for subnet_id, subnet in resources.items():
                    if subnet['type'] == 'aws_subnet' and subnet['name'] in subnet_refs_str:
                        containment_relationships.append((subnet_id, resource_id, "hosts"))
        
        elif resource_type == 'aws_ecs_service':
            # ECS services are in ECS clusters
            if 'cluster' in resource['config']:
                cluster_ref = resource['config']['cluster']
                for cluster_id, cluster in resources.items():
                    if cluster['type'] == 'aws_ecs_cluster' and extract_references_from_string(str(cluster_ref)):
                        containment_relationships.append((cluster_id, resource_id, "runs"))
            
            # ECS services use task definitions
            if 'task_definition' in resource['config']:
                task_ref = resource['config']['task_definition']
                for task_id, task in resources.items():
                    if task['type'] == 'aws_ecs_task_definition' and extract_references_from_string(str(task_ref)):
                        relationships.append((resource_id, task_id, "uses"))
        
        elif resource_type == 'aws_lb_target_group':
            # Connect target groups to their targets (usually ECS services)
            for ecs_id, ecs in resources.items():
                if ecs['type'] == 'aws_ecs_service':
                    if 'load_balancer' in ecs['config']:
                        lb_config = str(ecs['config']['load_balancer'])
                        if resource['name'] in lb_config:
                            relationships.append((resource_id, ecs_id, "routes to"))
    
    # Combine both types of relationships
    all_relationships = relationships + containment_relationships
    return all_relationships

def identify_nested_resources(resources: Dict[str, Any], relationships: List[Tuple[str, str, str]]) -> Dict[str, List[str]]:
    """
    Identify which resources should be nested inside others in the diagram.
    
    Args:
        resources: Dictionary of parsed Terraform resources
        relationships: List of resource relationships
        
    Returns:
        Dictionary mapping container resources to lists of contained resources
    """
    containers = {}
    
    # Identify resources that can act as containers
    for resource_id, resource in resources.items():
        resource_type = resource['type']
        if resource_type in AWS_RESOURCE_TYPES and AWS_RESOURCE_TYPES[resource_type].get('container', False):
            containers[resource_id] = []
    
    # Find containment relationships
    for source_id, target_id, rel_type in relationships:
        if source_id in containers and rel_type in ['contains', 'hosts', 'runs']:
            containers[source_id].append(target_id)
    
    # Find implied containment based on AWS architecture
    for resource_id, resource in resources.items():
        resource_type = resource['type']
        # Check if this resource has a defined parent type
        if resource_type in AWS_RESOURCE_TYPES and 'parent' in AWS_RESOURCE_TYPES[resource_type]:
            parent_type = AWS_RESOURCE_TYPES[resource_type]['parent']
            
            # Special case for subnets in VPCs
            if parent_type == 'vpc':
                for vpc_id, vpc in resources.items():
                    if vpc['type'] == 'aws_vpc':
                        # Check if there's a relationship between this subnet and the VPC
                        for source, target, _ in relationships:
                            if (source == resource_id and target == vpc_id) or (source == vpc_id and target == resource_id):
                                if vpc_id in containers:
                                    containers[vpc_id].append(resource_id)
            
            # Special case for ECS services in clusters
            elif parent_type == 'ecs_cluster':
                for cluster_id, cluster in resources.items():
                    if cluster['type'] == 'aws_ecs_cluster':
                        # Check if there's a relationship between this service and the cluster
                        for source, target, _ in relationships:
                            if (source == resource_id and target == cluster_id) or (source == cluster_id and target == resource_id):
                                if cluster_id in containers:
                                    containers[cluster_id].append(resource_id)
    
    return containers

def generate_enhanced_diagram(resources: Dict[str, Any], relationships: List[Tuple[str, str, str]], output_file: str):
    """
    Generate an enhanced AWS-style diagram with proper nested structure.
    
    Args:
        resources: Dictionary of parsed Terraform resources
        relationships: List of resource relationships
        output_file: Output file path for the diagram
    """
    # Create a new directed graph
    dot = gv.Digraph(comment='AWS Infrastructure')
    
    # Set graph attributes for AWS-style look with xlabels for orthogonal edges
    dot.attr('graph', rankdir='TB', pad='0.5', nodesep='0.75', ranksep='1.0', splines='ortho')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial', fontsize='12', margin='0.3,0.2')
    dot.attr('edge', fontname='Arial', fontsize='10', color='#666666', labelfloat='true')
    
    # Identify nested resources
    containers = identify_nested_resources(resources, relationships)
    
    # Create subgraphs for organization by service type
    service_groups = {}
    for resource_id, resource in resources.items():
        resource_type = resource['type']
        if resource_type in AWS_RESOURCE_TYPES:
            group = AWS_RESOURCE_TYPES[resource_type].get('group', 'other')
            if group not in service_groups:
                service_groups[group] = []
            service_groups[group].append(resource_id)
    
    # Define rank groupings to maintain reasonable layout structure
    rank_same_groups = []
    
    # Process VPC containers first (highest level)
    for vpc_id, members in containers.items():
        if resources[vpc_id]['type'] == 'aws_vpc':
            with dot.subgraph(name=f"cluster_{vpc_id}") as c:
                vpc_name = resources[vpc_id]['name']
                c.attr(label=f"VPC: {vpc_name}", style='filled', color='#333333', fillcolor='#F9DFCB20', 
                       fontsize='14', fontcolor='#333333', penwidth='2')
                
                # Add all resources that belong to this VPC
                for member_id in members:
                    if member_id in resources:
                        resource_type = resources[member_id]['type']
                        if resource_type in AWS_RESOURCE_TYPES:
                            attrs = AWS_RESOURCE_TYPES[resource_type]
                            label = f"{attrs['label']}\n{resources[member_id]['name']}"
                            c.node(member_id, label=label, shape=attrs['shape'], 
                                  style='filled', fillcolor=attrs['color'])
    
    # Process ECS clusters
    for cluster_id, members in containers.items():
        if resources[cluster_id]['type'] == 'aws_ecs_cluster':
            with dot.subgraph(name=f"cluster_{cluster_id}") as c:
                cluster_name = resources[cluster_id]['name']
                c.attr(label=f"ECS Cluster: {cluster_name}", style='filled', color='#333333', 
                       fillcolor='#FFE6CC20', fontsize='14', fontcolor='#333333', penwidth='2')
                
                # Add all resources that belong to this cluster
                for member_id in members:
                    if member_id in resources:
                        resource_type = resources[member_id]['type']
                        if resource_type in AWS_RESOURCE_TYPES:
                            attrs = AWS_RESOURCE_TYPES[resource_type]
                            label = f"{attrs['label']}\n{resources[member_id]['name']}"
                            c.node(member_id, label=label, shape=attrs['shape'], 
                                  style='filled', fillcolor=attrs['color'])
    
    # Add any resources not in containers
    contained_resources = set()
    for container_members in containers.values():
        contained_resources.update(container_members)
    
    for resource_id, resource in resources.items():
        if resource_id not in contained_resources and resource_id not in containers:
            resource_type = resource['type']
            if resource_type in AWS_RESOURCE_TYPES:
                attrs = AWS_RESOURCE_TYPES[resource_type]
                label = f"{attrs['label']}\n{resource['name']}"
                dot.node(resource_id, label=label, shape=attrs['shape'], 
                         style='filled', fillcolor=attrs['color'])
    
    # Add edges between resources with xlabels
    for source_id, target_id, rel_type in relationships:
        # Only show connections if they're not containment relationships
        if rel_type not in ['contains', 'hosts', 'runs'] or (source_id not in containers or target_id not in containers[source_id]):
            # Customize edge style based on relationship type
            if rel_type == 'references':
                dot.edge(source_id, target_id, style="dashed", xlabel="")
            else:
                # Use xlabel instead of label for compatibility with orthogonal edges
                dot.edge(source_id, target_id, xlabel=rel_type, fontsize="10")
    
    # Render the diagram with various format options
    try:
        dot.render(output_file, format='png', cleanup=True)
        print(f"Diagram generated: {output_file}.png")
        
        # Also generate SVG for better quality
        dot.render(f"{output_file}_svg", format='svg', cleanup=True)
        print(f"SVG diagram also generated: {output_file}_svg.svg")
    except Exception as e:
        print(f"Error generating diagram: {e}")
        # Try to save the DOT file at least
        try:
            with open(f"{output_file}.dot", "w") as f:
                f.write(dot.source)
            print(f"DOT file saved: {output_file}.dot")
        except Exception as e2:
            print(f"Error saving DOT file: {e2}")
            
def main():
    """Main function to parse arguments and execute the diagram generation."""
    parser = argparse.ArgumentParser(description='Generate AWS architecture diagrams from Terraform files')
    parser.add_argument('directory', help='Directory containing Terraform files')
    parser.add_argument('-o', '--output', default='aws_diagram', help='Output file name (without extension)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--style', choices=['default', 'aws'], default='aws', help='Diagram style (default or aws-style)')
    args = parser.parse_args()
    
    print(f"Analyzing Terraform files in: {args.directory}")
    
    # Parse Terraform files
    resources = parse_terraform_files(args.directory)
    print(f"Found {len(resources)} resources")
    
    # Debug output
    if args.debug:
        print("\nResources found:")
        for resource_id, resource in resources.items():
            print(f"  {resource_id} ({resource['file']})")
    
    # Extract relationships between resources
    relationships = extract_relationships(resources)
    print(f"Found {len(relationships)} relationships between resources")
    
    # Debug output
    if args.debug:
        print("\nRelationships found:")
        for source, target, rel_type in relationships:
            print(f"  {source} -> {target} ({rel_type})")
    
    # Generate the diagram
    if args.style == 'aws':
        generate_enhanced_diagram(resources, relationships, args.output)
    else:
        # Fall back to original diagram style
        from original_script import generate_diagram
        generate_diagram(resources, relationships, args.output)

if __name__ == '__main__':
    main()