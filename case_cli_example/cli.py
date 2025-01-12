#!/usr/bin/env python3

# Portions of this file contributed by NIST are governed by the
# following statement:
#
# This software was developed at the National Institute of Standards
# and Technology by employees of the Federal Government in the course
# of their official duties. Pursuant to Title 17 Section 105 of the
# United States Code, this software is not subject to copyright
# protection within the United States. NIST assumes no responsibility
# whatsoever for its use by other parties, and makes no guarantees,
# expressed or implied, about its quality, reliability, or any other
# characteristic.
#
# We would appreciate acknowledgement if the software is used.

"""
CASE CLI Example Tool - DNS Record Processor

This script demonstrates how to:
1. Process structured data (CSV) into CASE/UCO format
2. Create and link different CASE observable objects
3. Handle temporal data in CASE
4. Generate proper facets for domain names and IP addresses
5. Output CASE-compliant JSON-LD
6. Validate output against CASE ontology

The script specifically handles passive DNS records, showing how to:
- Map CSV columns to CASE properties
- Create DNSRecord objects with appropriate facets
- Link related objects using CASE relationships
- Handle timestamps and data typing
- Structure output following CASE conventions
- Validate CASE compliance
"""

import argparse
import logging
import csv
import sys
from datetime import datetime
from typing import Dict, List
from pathlib import Path

import cdo_local_uuid
from case_utils.namespace import NS_RDF, NS_UCO_CORE, NS_UCO_OBSERVABLE, NS_XSD
from pyshacl import validate
from cdo_local_uuid import local_uuid
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.util import guess_format

def process_dns_records(csv_file: str, ns_kb: Namespace, graph: Graph) -> None:
    """
    Process DNS records from CSV and add them to the RDF graph following CASE ontology.
    
    This function demonstrates:
    - Creating CASE DNSRecord objects with UUID identifiers
    - Adding appropriate facets (DomainName and IPv4Address)
    - Setting temporal properties
    - Handling passive DNS specific attributes
    - Creating relationships between domain names and IP addresses using proper vocabulary
    
    Args:
        csv_file: Path to CSV file containing DNS records
        ns_kb: Namespace for knowledge base individuals
        graph: RDF graph to add the records to
    
    CSV Format Expected:
        observable:DomainName: Domain name string (all .org TLD)
        core:kindOfRelationship: Type of relationship ("resolves to")
        observable:IPv4Address: IPv4 address string
        observable:timeDateStamp: Timestamp in ISO format
    """
    # Add vocabulary namespace
    NS_UCO_VOCABULARY = Namespace("https://ontology.unifiedcyberontology.org/uco/vocabulary/")
    graph.namespace_manager.bind("vocabulary", NS_UCO_VOCABULARY)

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Create DNS Record node with UUID
            dns_record_id = ns_kb[f"DNSRecord-{local_uuid()}"]
            
            # Add DNS Record type - fundamental CASE typing
            graph.add((dns_record_id, NS_RDF.type, NS_UCO_OBSERVABLE.DNSRecord))
            
            # Add observation time - when this DNS resolution was observed
            graph.add((
                dns_record_id, 
                NS_UCO_CORE.observationTime, 
                Literal(row['observable:timeDateStamp'], datatype=NS_XSD.dateTime)
            ))
            
            # Add DNS-specific properties
            graph.add((
                dns_record_id,
                NS_UCO_OBSERVABLE.recordType,
                Literal("A")
            ))
            graph.add((
                dns_record_id,
                NS_UCO_OBSERVABLE.isPassiveDNS,
                Literal(True)
            ))

            # Create Domain Name Facet with UUID
            domain_facet_id = ns_kb[f"DomainNameFacet-{local_uuid()}"]
            graph.add((domain_facet_id, NS_RDF.type, NS_UCO_OBSERVABLE.DomainNameFacet))
            graph.add((
                domain_facet_id,
                NS_UCO_OBSERVABLE.value,  # Using value property as per mappings
                Literal(row['observable:DomainName'])
            ))
            
            # Create IPv4 Address Facet with UUID
            ip_facet_id = ns_kb[f"IPv4AddressFacet-{local_uuid()}"]
            graph.add((ip_facet_id, NS_RDF.type, NS_UCO_OBSERVABLE.IPv4AddressFacet))
            graph.add((
                ip_facet_id,
                NS_UCO_OBSERVABLE.addressValue,  # Using addressValue property as per mappings
                Literal(row['observable:IPv4Address'])
            ))
            
            # Link facets to DNS Record
            graph.add((dns_record_id, NS_UCO_CORE.hasFacet, domain_facet_id))
            graph.add((dns_record_id, NS_UCO_CORE.hasFacet, ip_facet_id))

            # Create relationship between domain and IP using proper vocabulary
            relationship_id = ns_kb[f"Relationship-{local_uuid()}"]
            graph.add((relationship_id, NS_RDF.type, NS_UCO_CORE.Relationship))
            graph.add((relationship_id, NS_UCO_CORE.source, domain_facet_id))
            graph.add((relationship_id, NS_UCO_CORE.target, ip_facet_id))
            # Add required isDirectional property
            graph.add((
                relationship_id,
                NS_UCO_CORE.isDirectional,
                Literal(True)
            ))
            # Add kindOfRelationship as a string
            graph.add((
                relationship_id,
                NS_UCO_CORE.kindOfRelationship,
                Literal("Resolved_To")
            ))

def validate_case_output(output_file: str) -> bool:
    """
    Validate the generated CASE JSON-LD output using PyShacl with UCO ontology.
    The SHACL rules are embedded in the ontology TTL files.
    """
    try:
        # Load the data graph
        data_graph = Graph()
        data_graph.parse(output_file, format="json-ld")
        
        # Load UCO ontology (which includes SHACL shapes)
        ont_graph = Graph()
        
        # Try loading each ontology file separately with error reporting
        urls = {
            "core.ttl": "https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/core/core.ttl",
            "observable.ttl": "https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/observable/observable.ttl"
        }
        
        for name, url in urls.items():
            try:
                ont_graph.parse(url, format="turtle")
                logging.info(f"Successfully loaded {name}")
            except Exception as e:
                logging.error(f"Failed to load {name} from {url}")
                logging.error(f"Error: {str(e)}")
                return False
        
        # Run validation using the ontology graph as both ontology and SHACL shapes
        conforms, results_graph, results_text = validate(
            data_graph,
            shacl_graph=ont_graph,  # Use ontology graph for SHACL shapes
            ont_graph=ont_graph,
            inference='rdfs',
            abort_on_first=False,
            meta_shacl=False,
            debug=False
        )
        
        if conforms:
            logging.info("Graph conforms to UCO/CASE ontology")
        else:
            logging.error("Validation Results:")
            logging.error(results_text)
        
        return conforms
        
    except Exception as e:
        logging.error(f"Validation error: {str(e)}")
        logging.debug("Stack trace:", exc_info=True)
        return False

def main() -> None:
    """
    Main function demonstrating CASE CLI tool construction.
    
    Shows:
    - Command line argument handling
    - CASE graph initialization
    - Namespace management
    - Data processing
    - Output serialization
    - CASE validation
    """
    argument_parser = argparse.ArgumentParser(
        description="CASE CLI Example - Process DNS records into CASE format"
    )
    argument_parser.add_argument(
        "--kb-prefix",
        default="kb",
        help="Prefix label to use for knowledge-base individuals."
    )
    argument_parser.add_argument(
        "--kb-prefix-iri",
        default="http://example.org/kb/",
        help="Prefix IRI to use for knowledge-base individuals."
    )
    argument_parser.add_argument("--debug", action="store_true")
    argument_parser.add_argument(
        "--output-format", 
        help="Override extension-based format guesser."
    )
    argument_parser.add_argument(
        "out_graph",
        help="A self-contained RDF graph file."
    )
    argument_parser.add_argument(
        "--dns-csv",
        help="Input CSV file containing DNS records.",
        default="data/domain-ip-res.csv"
    )
    argument_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the output against CASE ontology"
    )

    args = argument_parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    # Configure UUID generation
    cdo_local_uuid.configure()
    
    # Initialize namespace and graph
    ns_kb = Namespace(args.kb_prefix_iri)
    graph = Graph()

    # Bind namespaces
    graph.namespace_manager.bind(args.kb_prefix, ns_kb)
    graph.namespace_manager.bind("uco-core", NS_UCO_CORE)
    graph.namespace_manager.bind("uco-observable", NS_UCO_OBSERVABLE)
    graph.namespace_manager.bind("xsd", NS_XSD)

    # Process DNS records
    process_dns_records(args.dns_csv, ns_kb, graph)

    # Determine output format
    output_format = (
        guess_format(args.out_graph)
        if args.output_format is None
        else args.output_format
    ) or "json-ld"
    
    # Write output file
    graph.serialize(
        destination=args.out_graph,
        format=output_format,
        context={
            "uco-core": "https://ontology.unifiedcyberontology.org/uco/core/",
            "uco-observable": "https://ontology.unifiedcyberontology.org/uco/observable/",
            "xsd": "http://www.w3.org/2001/XMLSchema#"
        }
    )

    # Validate if requested
    if args.validate:
        logging.info("Validating output against CASE ontology...")
        if validate_case_output(args.out_graph):
            logging.info("Validation successful!")
        else:
            logging.error("Validation failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()
