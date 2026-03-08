from setuptools import setup, find_packages

setup(
    name="cloud-cspm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "boto3>=1.28.0",
        "pyyaml>=6.0",
        "rich>=13.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "jinja2>=3.1.0",
        "python-multipart>=0.0.9",
    ],
    entry_points={
        "console_scripts": [
            "cspm=cspm.cli:main",
        ],
    },
)
