#!/usr/bin/env python3
import os

import aws_cdk as cdk

from llm_mlops_infra.llm_mlops_stack import LLmMlopsStack


app = cdk.App()

# Existing stack
LLmMlopsStack(app, "LLmMlopsStack")

app.synth()
