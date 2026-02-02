#!/usr/bin/env python3
import os

import aws_cdk as cdk

from llm_mlops_infra.llm_mlops_stack import LLmMlopsStack
from llm_mlops_infra.audio_ingestion_stack import AudioIngestionStack

app = cdk.App()

# Existing stack
LLmMlopsStack(app, "LLmMlopsStack")
AudioIngestionStack(app, "AudioIngestionStack")


app.synth()
