#!/usr/bin/env python
from distutils.core import setup
setup(name="GF",
    version="0.2",
    description="Python interface for GF file of FrontFlow/Blue,"
    " and utils for converting GF to LSV Uns format",
    requires=["numpy"],
    author="Yoshikawa, Hiroyuki, FUJITSU LTD.",
    author_email="yoh@jp.fujitsu.com",
    packages=["GF"],
    )

