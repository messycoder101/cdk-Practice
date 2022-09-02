import json



def handler(event, context):
    print(' request: {}'.format(json.dumps(event)))
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plan'
        },
        
        'body': 'Hello, CDK! hotswap 3 You have hit {}'.format(event['path'])
    }