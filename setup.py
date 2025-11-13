"""Setup configuration for HiyaDrive."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hiya-drive",
    version="0.1.0",
    author="HiyaDrive Team",
    description="AI Voice Booking Agent for Drivers - Hands-free restaurant reservations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/hiya-drive",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.9",
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    entry_points={
        "console_scripts": [
            "hiya-drive=hiya_drive.main:cli",
        ],
    },
)
