from setuptools import find_packages, setup

setup(
    name="source-prospect-crm",
    description="Airbyte source connector for Prospect CRM (OData v1).",
    author="Harper Grace International",
    author_email="data@hgi.com",
    packages=find_packages(),
    install_requires=["airbyte-cdk>=0.51.0,<1.0.0", "requests>=2.28.0"],
    package_data={"source_prospect_crm": ["spec.yaml"]},
    python_requires=">=3.9",
)
