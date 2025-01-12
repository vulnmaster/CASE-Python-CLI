# Domain-IP Resolution Data Mappings to CASE/UCO

## Data Type Context
The data represents passive DNS resolution records that capture historical DNS resolution states without active querying. This maps to CASE/UCO's `observable:DNSRecord` type with temporal context.

## Core Object Type
- Primary Type: `observable:DNSRecord`
  - Represents a passive DNS record observation
  - Contains both the domain and IP address relationship
  - Includes temporal metadata about when the resolution was observed

## Column Mappings

1. `observable:DomainName` column:
   - Maps to `observable:DomainName` object
   - Property: `observable:value` contains the domain string (all .org TLD)
   - Connected to DNSRecord via `core:hasFacet`

2. `core:kindOfRelationship` column:
   - Maps to relationship type between domain and IP
   - Value "resolves to" indicates DNS A record relationship
   - Represented in CASE through the DNSRecord object type and recordType property

3. `observable:IPv4Address` column:
   - Maps to `observable:IPv4Address` object
   - Property: `observable:addressValue` contains the IP value
   - Connected to DNSRecord via `core:hasFacet`
   - Type: IPv4Address (based on format)

4. `observable:timeDateStamp` column:
   - Maps to `core:observationTime` on the DNSRecord object
   - Represents when this passive DNS observation was made
   - Uses xsd:dateTime format as required by CASE

## Relationship Structure
```json
{
  "@context": {
    "uco-core": "https://ontology.unifiedcyberontology.org/uco/core/",
    "uco-observable": "https://ontology.unifiedcyberontology.org/uco/observable/",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "uco-observable:DNSRecord",
  "uco-core:observationTime": {
    "@type": "xsd:dateTime",
    "@value": "2023-12-01T10:00:00Z"
  },
  "uco-core:hasFacet": [
    {
      "@type": "uco-observable:DomainNameFacet",
      "uco-observable:value": "example.org"
    },
    {
      "@type": "uco-observable:IPv4AddressFacet",
      "uco-observable:addressValue": "192.168.1.1"
    }
  ],
  "uco-observable:recordType": "A",
  "uco-observable:isPassiveDNS": true
}
```

## Additional Context Properties
- `observable:recordType`: Set to "A" for IPv4 address records (conforming to DNS record type standards)
- `observable:isPassiveDNS`: Boolean flag indicating this is a passive DNS observation
- `core:description`: Optional context about passive DNS collection methodology

## Temporal Properties
- `core:observationTime`: Represents when the DNS resolution was observed (primary timestamp)
- `core:objectCreatedTime`: When the record was created in the system (if needed)
- `core:modifiedTime`: If/when the record is updated
- Historical tracking supported through multiple DNSRecord objects with different observation times

## Namespace Context
The mapping uses the following key namespaces:
- `uco-core`: https://ontology.unifiedcyberontology.org/uco/core/
- `uco-observable`: https://ontology.unifiedcyberontology.org/uco/observable/
- `xsd`: http://www.w3.org/2001/XMLSchema#