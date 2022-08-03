#!/usr/bin/env python

import setuptools
import os, shutil

def copytree(src, dst):
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d)
        else:
            shutil.copy(s, d)

def reqs_from_file(src):
    requirements = []
    with open(src) as f:
        for line in f:
            line = line.strip()
            if not line.startswith("-r"):
                requirements.append(line)
            else:
                add_src = line.split(' ')[1]
                add_req = reqs_from_file(add_src)
                requirements.extend(add_req)
    return requirements

if __name__ == "__main__":

    with open("docs/README.md", "r") as fh:
        long_description = fh.read()

    requirements=[]
    wd = os.path.dirname(os.path.abspath(__file__))

    copytree("third_party/preprocess/moses", os.path.join(wd, "monotextor/data/moses"))
    requirements = reqs_from_file("requirements.txt")

    setuptools.setup(
        name="monotextor",
        version="1.0.0",
        install_requires=requirements,
        license="GNU General Public License v3.0",
        #author=,
        #author_email=,
        #maintainer=,
        #maintainer_email,
        description="Bitextor generates translation memories from multilingual websites",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/bitextor/monotextor",
        packages=["monotextor", "monotextor.utils"],
        #classifiers=[],
        #project_urls={},
        package_data={
            "monotextor": [
                "Snakefile",
                "rules/*",
                "utils/clean-corpus-n.perl",
                "data/*",
                "data/model/*",
                "data/moses/ems/support/*",
                "data/moses/tokenizer/*",
                "data/moses/share/nonbreaking_prefixes/*",
            ]
        },
        entry_points={
            "console_scripts": [
                "monotextor = monotextor.monotextor_cli:main",
                "monotextor-full = monotextor.monotextor_cli:main_full"
            ]
        }
        )
