[September 1, 2022, 3:25 PM] Samani, Bahram: import json
import os


import boto3


ddb = boto3.resource('dynamodb')
table = ddb.Table(os.environ['HITS_TABLE_NAME'])
_lambda = boto3.client('lambda')

def handler(event, context):
    print('request: {}'.format(json.dumps(event)))
    table.update_item(
        Key={'path': event['path']},
        UpdateExpression='ADD hits :incr',
        ExpressionAttributeValues={':incr':1}
        
    )
    
    resp = _lambda.invoke(
        FunctionName=os.environ['DOWNSTREAM_FUNCTION_NAME'],
        Payload=json.dumps(event),
    )
    
    body = resp['Payload'].read()
    
    print('downstream reponse: {}'.format(body))
    return json.loads(body)
    
    
    
[September 1, 2022, 3:27 PM] Samani, Bahram: from constructs import Construct
from aws_cdk import (
    aws_lambda as _lambda,    
    aws_dynamodb as ddb,
    RemovalPolicy,
)



class HitCounter(Construct):
    
    @property
    def handler(self):
        return self._handler
        
    @property
    def table(self):
        return self._table
    
    def __init__(self, scope: Construct, id: str, downstream: _lambda.IFunction, read_capacity: int = 5, **kwargs):
        if read_capacity < 5 or read_capacity > 20:
            raise ValueError("Read capacity must be greater than 5 and less than 20")
        
        super().__init__(scope, id, **kwargs)
        
        self._table = ddb.Table(
            self, 'Hits',
            partition_key={'name': 'path', 'type': ddb.AttributeType.STRING},
            encryption=ddb.TableEncryption.AWS_MANAGED,
            read_capacity=read_capacity,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        self._handler = _lambda.Function(
            self, 'HitCounterHandler',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='hitcount.handler',
            code=_lambda.Code.from_asset('lambda/python'),
            environment = {
                'DOWNSTREAM_FUNCTION_NAME': downstream.function_name,
                'HITS_TABLE_NAME':self._table.table_name,
            }
            
        )
        
        self._table.grant_read_write_data(self._handler)
        downstream.grant_invoke(self._handler)
        
    
        
        
        
        
        
[September 1, 2022, 3:28 PM] Samani, Bahram: from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    assertions,
    
)

from cdk_workshop.hitcounter import HitCounter
import pytest

def test_dyanmodb_table_created():
    stack = Stack()
    HitCounter(stack, 'HitCounter',
        downstream=_lambda.Function(stack, 'TestFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='hello.handler',
            code=_lambda.Code.from_asset('lambda/python'))
    )
    
    template=assertions.Template.from_stack(stack)
    template.resource_count_is('AWS::DynamoDB::TABLE',0)
    
    
def test_lambda_function_hitcounter():
    stack=Stack()
    HitCounter(stack, 'HitCounter',
        downstream=_lambda.Function(stack, 'TestFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='hello.handler',
            code=_lambda.Code.from_asset('lambda/python'))
    )
    
    template = assertions.Template.from_stack(stack)
    envCapture = assertions.Capture()
    
    template.has_resource_properties("AWS::Lambda::Function",{
        "Handler":"hitcount.handler",
        "Environment":envCapture
        }
    )
    
    assert envCapture.as_object() == {
        "Variables": {
            "DOWNSTREAM_FUNCTION_NAME": {"Ref": "TestFunction22AD90FC"},
            "HITS_TABLE_NAME": {"Ref": "HitCounterHits079767E5"}
        }
    }
    
def test_dynamodb_with_encryption():
    stack = Stack()
    HitCounter(stack, 'HitCounter',
        downstream=_lambda.Function(stack, 'TestFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='hello.handler',
            code=_lambda.Code.from_asset('lambda/python'))
    )
    
    template = assertions.Template.from_stack(stack)
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "SSESpecification": {
            "SSEEnabled": True,
        },
    })
    
def test_dynamo_raises_read_capacity():
    stack= Stack()
    with pytest.raises(Exception):
        HitCounter(stack, 'HitCounter',
            downstream=_lambda.Function(stack, 'TestFunction',
                runtime=_lambda.Runtime.PYTHON_3_9,
                handler='hello.handler',
                code=_lambda.Code.from_asset('lambda/python')),
            read_capacity=1,
            )