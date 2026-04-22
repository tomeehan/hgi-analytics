import sys

from airbyte_cdk.entrypoint import launch

from source_prospect_crm import SourceProspectCrm

if __name__ == "__main__":
    source = SourceProspectCrm()
    launch(source, sys.argv[1:])
