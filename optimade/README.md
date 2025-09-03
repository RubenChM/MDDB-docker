# Optimade

The **Open Databases Integration for Materials Design** (OPTIMADE) consortium aims to make materials databases interoperable by developing a specification for a common REST API.

https://github.com/JPBergsma/optimade-python-tools.git

## Dockerfile

```Dockerfile
FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Define build arguments
ARG OPTIMADE_INNER_PORT
ARG DB_AUTH_USER
ARG DB_AUTH_PASSWORD
ARG DB_SERVER
ARG DB_PORT
ARG DB_NAME
ARG DB_AUTHSOURCE
ARG PROTOCOL
ARG URL

# Define working dir
WORKDIR /app

# Clone and install optimade-python-tools
RUN git clone https://github.com/JPBergsma/optimade-python-tools.git && \
    cd optimade-python-tools && \
    git checkout JPBergsma_BioExcel && \
    pip install -e .[server]

# Define working dir
WORKDIR /app/optimade-python-tools

# Copy the current directory contents into the container at /app
COPY .optimade.json /root/.optimade.json

# Perform search and replace using sed
RUN sed -i "s/DB_AUTH_USER/${DB_AUTH_USER}/g" /root/.optimade.json
RUN sed -i "s/DB_AUTH_PASSWORD/${DB_AUTH_PASSWORD}/g" /root/.optimade.json
RUN sed -i "s/DB_SERVER/${DB_SERVER}/g" /root/.optimade.json
RUN sed -i "s/DB_PORT/${DB_PORT}/g" /root/.optimade.json
RUN sed -i "s/DB_NAME/${DB_NAME}/g" /root/.optimade.json
RUN sed -i "s/DB_AUTHSOURCE/${DB_AUTHSOURCE}/g" /root/.optimade.json
RUN sed -i "s/PROTOCOL/${PROTOCOL}/g" /root/.optimade.json
RUN sed -i "s/URL/${URL}/g" /root/.optimade.json

# Expose the port where the app runs on
EXPOSE ${OPTIMADE_INNER_PORT}

# Define environment variable
ENV OPTIMADE_INNER_PORT=${OPTIMADE_INNER_PORT}

# Serve the app using exec form with shell expansion
CMD ["sh", "-c", "uvicorn optimade.server.main:app --reload --host 0.0.0.0 --port $OPTIMADE_INNER_PORT"]
```

## Config file (.optimade.json)

```json
{
    "database_backend": "mongodb",
    "mongo_uri": "mongodb://DB_AUTH_USER:DB_AUTH_PASSWORD@DB_SERVER:DB_PORT/?authSource=DB_AUTHSOURCE",
    "mongo_database": "DB_NAME",
    "structures_collection": "topologies",
    "trajectories_collection": "projects",
    "insert_test_data": false,
    "debug": true,
    "default_db": "test_server",
    "root_path": "/optimade",
    "implementation": {
        "name": "MDPOSIT implementation",
        "source_url": "https://github.com/Materials-Consortia/optimade-python-tools",
        "issue_tracker": "https://github.com/Materials-Consortia/optimade-python-tools/issues",
        "maintainer": {"email": "daniel.beltran@irbbarcelona.org"}
    },
    "provider": {
        "name": "IRB Barcelona",
        "description": "A database with molecular dynamics for biological molecules",
        "prefix": "bioxl",
	"homepage": "PROTOCOL://URL"
    },
    "provider_homepage": {
	    "PROTOCOL://URL/optimade": "PROTOCOL://URL"
    },
    "provider_fields": {
        "trajectories": [{
                "name": "metadata.TIMESTEP",
                "description": "The timestep between frames of the trajectory.",
                "unit": "ps",
                "type": "float"
            },{
                "name": "metadata.LENGTH",
                "description": "The duration of the trajectory",
                "unit": "ns",
                "type": "float"
            },{
                "name": "metadata.FF",
                "description": "Forcefields used to model the molecular dynamics",
                "type": "list"
            },{
                "name": "metadata.TEMP",
                "description": "Temperature used to model the molecular dynamics",
                "unit": "K",
                "type": "float"
            },{
                "name": "metadata.PROGRAM",
                "description": "Name of the software used to model the molecular dynamics",
                "type": "string"
            },{
                "name": "metadata.VERSION",
                "description": "Version of the software used to model the molecular dynamics",
                "type": "string"
            },{
                "name": "metadata.LICENCE",
                "description": "Use license for simulation data",
                "type": "string"
            },{
                "name": "metadata.LINKCENSE",
                "description": "Link to use license for simulation data",
                "type": "string"
            },{
                "name": "metadata.CITATION",
                "description": "Reference to cite the simulation data",
                "type": "string"
            },{
                "name": "metadata.DESCRIPTION",
                "description": "Description of the simulation",
                "type": "string"
            },{
                "name": "metadata.GROUPS",
                "description": "Groups involved in the modelling of the simulation",
                "type": "string"
            },{
                "name": "metadata.CONTACT",
                "description": "Reference to contact the simulation authors (e.g. mail)",
                "type": "string"
            },{
                "name": "metadata.THANKS",
                "description": "Acknowledgements from the authors",
                "type": "string"
            },{
                "name": "metadata.PDBIDS",
                "description": "PDB ids of structures used in the modelling of the simulation",
                "type": "list"
            },{
                "name": "metadata.METHOD",
                "description": "Method used in the modelling of the simulation (e.g. Classical MD, Enhanced sampling, etc.)",
                "type": "string"
            },{
                "name": "metadata.TYPE",
                "description": "Type of molecular dynamics ('trajectory' or 'ensemble')",
                "type": "string"
            },{
                "name": "metadata.LINKS",
                "description": "URL links to simulation related web sites",
                "type": "list"
            },{
                "name": "metadata.AUTHORS",
                "description": "Simulation authors",
                "type": "string"
            },{
                "name": "residues",
                "description": "**For each residue in the system there is a dictionary that describes this residue. Residues are groups of related atoms (e.g. an aminoacid). \n  Databases are allowed to add more properties as long as the properties are prefixed with the database specific prefix.\n- **Type**: list of dictionaries with the properties:\n   - :property:`name`: string (REQUIRED)\n    - :property:`number`: integer (REQUIRED)\n    - :property:`icode`: string or null (REQUIRED)\n    - :property:`chain`: string (OPTIONAL)\n- **Requirements/Conventions**:\n   - **Query**:  Support for queries on this property is OPTIONAL.\n     If supported, only a subset of the filter features MAY be supported.\n   - **name**: The residue name\n   - **number**: The residue number according to source notation.\n   - **icode**: The residue insertion code. It MUST NOT be longer than 1 character. It MAY be null.\n   - **chain**: The chain number this residue belongs to.\n   - Values in :property:`chain` SHOULD be in capital letters.\n   - Values in :property:`chain` SHOULD NOT be longer than 1 character when the number of chains is not greater than the number of letters in English alphabet (26).\n   - All :property:`name` and :property:`icode` values SHOULD be in capital letters.",
                "type": "list"
            },{
                "name": "residues_at_sites",
                "description": "Index of the residue to which a site belongs. The values for sites are specified with the same order of the property `cartesian_site_positions`_.\n  The properties of the residues are found in the property `_biomol_residues`_.\n- **Type**: list of integers.\n- **Requirements/Conventions**:\n  - **Support**: MUST be supported when `_biomol_residues`_ is present as well, i.e., MUST NOT be :val:`null`.\n  - **Query**: Support for queries on this property is OPTIONAL.\n    If supported, filters MAY support only a subset of comparison operators.\n  - The number of values MUST be equal to :property: `nsites`, i.e. the number of sites in the structure.\n  - Each value in the `_biomol_residues_at_sites`_ list MUST correspond to  the index of one the dictionaries in the `_biomol_residues`_ list.",
                "type": "list"

	    }
        ],
        "references": ["orcid", "num_citations"]
    },
    "aliases": {
        "trajectories":{
          "id": "accession",
          "reference_structure.nsites": "metadata.atomCount",
          "nframes": "metadata.SNAPSHOTS"
        }
    },
    "length_aliases": {
        "structures": {
        }
    },
    "enabled_response_formats": ["json", "hdf5"],
    "max_response_size": {"json": 40, "hdf5": 200},
    "page_limit": 5,
    "exclude_from_reference_structure": ["cartesian_site_positions","species_at_sites"]
}

```