import boto3
import json
from datetime import date,datetime, timedelta

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

metrics= []

# metrics= [{'name': 'RDS CPU Utilization',
#            'request': {'Namespace':'AWS/RDS',
#                         'MetricName':'CPUUtilization',
#                         'StartTime': datetime.utcnow() - timedelta(minutes=10),
#                         'EndTime': datetime.now() ,
#                         'Period': 600,
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
#                        'Period': 600,
#                        'Statistics':['Average'],
#                        'Unit':'Percent'},
#            'statistics': 'Average',
#            'unit': 'Percent'},
#           {'name': 'ELB avg. response time',
#            'request': {'Namespace':'AWS/ApplicationELB',
#                        'MetricName':'TargetResponseTime',
#                        'Dimensions': [{'Name':'LoadBalancer','Value':'app/skart-Skart-ZQXTM8Q3E7MY/deb95921b4d7b0f8'}],
#                        'StartTime': datetime.utcnow() - timedelta(minutes=10),
#                        'EndTime': datetime.now() ,
#                        'Period': 600,
#                        'Statistics':['Average'],
#                        'Unit':'Seconds'},
#            'statistics': 'Average',
#            'unit': 'Seconds'}]



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


def filter_not_alarm(d):
    if d['State'] == "ALARM":
        return True
    return False

def map_alarm_history(d):
    return {'AlarmName': d['AlarmName'],
            'Timestamp': d['Timestamp'],
            'State': json.loads(d['HistoryData'])["newState"]['stateValue'],
            'HistoryData': json.loads(d['HistoryData'])}

def get_alarms_history():
    client = boto3.client('cloudwatch')
    start=datetime.utcnow() - timedelta(hours=24)
    end=datetime.utcnow()
    response = client.describe_alarm_history(StartDate=start,EndDate=end,HistoryItemType='StateUpdate')
    return (list(filter (filter_not_alarm, (map(map_alarm_history, response['AlarmHistoryItems'])))))


def get_commit_info(pipeline_status):
    # CodeCommit may fail sometimes so lets catch it
    try:
        code_commit = boto3.client('codecommit')
        artifact_url = pipeline_status['pipelineExecution']['artifactRevisions'][0]['revisionUrl']
        commit_id = artifact_url.split('/')[-1]
        git_repository = artifact_url.split('/')[-3]
        commit_info = code_commit.get_commit(repositoryName=git_repository, commitId=commit_id)
        author = commit_info['commit']['committer']['name']
        commit_message = commit_info['commit']['message']
        return {"commitAuthor": author,
                "commitMessage:": commit_message}
    except Exception:
        return {"commitAuthor": "",
                "commitMessage": ""}

        
def get_pipeline_current_status(pipeline):
    client = boto3.client('codepipeline')
    res = client.get_pipeline_state(name=pipeline)
    execution_id =  res['stageStates'][0]['latestExecution']['pipelineExecutionId']
    status = client.get_pipeline_execution(pipelineName=pipeline,pipelineExecutionId=execution_id)
    commit_info = get_commit_info(status)
    pipeline_status = {"currentStatus": status['pipelineExecution']['status']}
    return {**pipeline_status, **commit_info}


def map_statuses(d):
    return {'name': d['name'],
            **get_pipeline_current_status(d['name'])}


def get_pipelines():
    client = boto3.client('codepipeline')
    pipelines = client.list_pipelines()["pipelines"]
    return (list(map(map_statuses, pipelines)))


def status(event, context):
    result = {
        "alarms":get_alarms(),
        "pipelines" : get_pipelines(),
        "metrics" : get_metrics(),
        "alarms_history": get_alarms_history()}
    return {"body": json.dumps(result, default=json_serial)}
