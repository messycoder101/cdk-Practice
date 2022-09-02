#!/usr/bin/env python3

import aws_cdk as cdk

from cdk_workshop.pipeline_stack import WorkshopPipelineStack


app = cdk.App()
WorkshopPipelineStack(app, "cdk-workshop")

app.synth()