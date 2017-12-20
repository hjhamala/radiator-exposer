import boto3
import json
from datetime import datetime, timedelta

# metrics= [{'name': 'RDS CPU Utilization',
#            'request': {'Namespace':'AWS/RDS',
#                         'MetricName':'CPUUtilization',
#                         'StartTime': datetime.utcnow() - timedelta(minutes=10),
#                         'EndTime': datetime.now() ,
#                         'Period': 1200,
#                         'Statistics':['Average'],
#                         'Unit':'Percent'},
#            'statistics': 'Average',
#            'unit': 'Percent'},
#           {'name': 'ECS CPU Utilization',
#            'request': {'Namespace':'AWS/ECS',
#                        'MetricName':'CPUUtilization',
#                        'Dimensions': [{'Name':'ClusterName','Value':'skartta'}],
#                        'StartTime': datetime.utcnow() - timedelta(minutes=10),
#                        'EndTime': datetime.now() ,
#                        'Period': 1200,
#                        'Statistics':['Average'],
#                        'Unit':'Percent'},
#            'statistics': 'Average',
#            'unit': 'Percent'}]

metrics= []

def get_metric(m):
    client = boto3.client('cloudwatch')
    return client.get_metric_statistics(**m)


def map_metric(m):
    try:
        return {'name': m['name'],
            'statistics': m['statistics'],
            'unit': m['unit'],
            'result': get_metric(m['request'])['Datapoints'][0][m['statistics']]}
    except Exception:
        return None

def get_metrics():
    return list(filter(None, (map(map_metric,metrics))))


def filter_alarm_keys(d):
    return {'AlarmName': d['AlarmName'],
            'StateValue': d['StateValue']}

def get_alarms():
    client = boto3.client('cloudwatch')
    alarms = client.describe_alarms()
    return (list(map(filter_alarm_keys, alarms['MetricAlarms'])))


def get_pipeline_current_status(pipeline):
    client = boto3.client('codepipeline')
    res = client.get_pipeline_state(name=pipeline)
    execution_id =  res['stageStates'][0]['latestExecution']['pipelineExecutionId']
    status = client.get_pipeline_execution(pipelineName=pipeline,pipelineExecutionId=execution_id)
    return status['pipelineExecution']['status']


def map_statuses(d):
    return {'name': d['name'],
            'currentStatus': get_pipeline_current_status(d['name'])}


def get_pipelines():
    client = boto3.client('codepipeline')
    pipelines = client.list_pipelines()["pipelines"]
    return (list(map(map_statuses, pipelines)))


def status(event, context):
    result = {
        "alarms":get_alarms(),
        "pipelines" : get_pipelines(),
        "metrics" : get_metrics()}
    return {"body": json.dumps(result)}
