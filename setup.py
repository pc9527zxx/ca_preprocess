from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="contract-preprocess",
    description="Compile Solidity/Vyper targets and output direct function call edges (A -> B).",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "packaging",
        "prettytable>=3.10.2",
        "pycryptodome>=3.4.6",
        "crytic-compile>=0.3.9,<0.4.0",
        "web3>=7.10,<8",
        "eth-abi>=5.0.1",
        "eth-typing>=5.0.0",
        "eth-utils>=5.0.0",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": [
            "contract-preprocess = contract_preprocess.tools.preprocess.__main__:main",
        ]
    },
)
