import base64
import json
import requests

from invoke import run


# TODO: generalize
def update_ranger_usersync(c):
    c.run('/usr/jdk64/jdk1.8.0_112/bin/java -Dlogdir=/var/log/ranger/usersync '
          '-cp "/usr/hdp/current/ranger-usersync/dist/'
          'unixusersync-0.7.0.2.6.5.0-292.jar:/usr/hdp/current/ranger-usersync'
          '/dist/ranger-usersync-1.0-SNAPSHOT.jar:/usr/hdp/current/'
          'ranger-usersync/lib/*:/etc/ranger/usersync/conf" '
          'org.apache.ranger.usergroupsync.UserGroupSyncTrigger')


def create_ranger_policy(c, resource, username, policy_name,
                         policy_description, resource_type, service):
    template = json.load(open('ranger_templates/{}.json'.format(service), 'r'))
    template['service'] = '{cluster_name}_{service}'.format(
        cluster_name=c.config.ranger_cluster_name, service=service)
    template['name'] = policy_name
    template['description'] = policy_description
    template['resources'][resource_type]['values'].extend(resource)
    template['policyItems'][0]['users'].append(username)

    run("curl -X POST {ranger_url}/service/public/v2/api/policy "
        "-H 'authorization: Basic {auth_token}' "
        "-H 'content-type: application/json' "
        "-d '{content}' -k".format(
            ranger_url=c.config.ranger_url,
            auth_token=base64.b64encode(
                '{ranger_user}:{ranger_password}'.format(
                    ranger_user=c.config.ranger_user,
                    ranger_password=c.config.ranger_password)),
            content=json.dumps(template))
        )


def update_nifi_flow_ranger_policy(c, username):
    response = requests.get(
        '{ranger_url}/service/public/v2/api/policy/{policy_id}'.format(
            ranger_url=c.config.ranger_url,
            policy_id=c.config.nifi_ranger_flow_policy_id),
        headers={'content-type': 'application/json'},
        auth=(c.config.ranger_user, c.config.ranger_password),
        verify=False)
    policy = response.json()
    policy['policyItems'][0]['users'].append(username)

    run("curl -X PUT {ranger_url}/service/public/v2/api/policy/{policy_id} "
        "-H 'authorization: Basic {auth_token}' "
        "-H 'content-type: application/json' "
        "-d '{content}' -k".format(
            ranger_url=c.config.ranger_url,
            policy_id=c.config.nifi_ranger_flow_policy_id,
            auth_token=base64.b64encode(
                '{ranger_user}:{ranger_password}'.format(
                    ranger_user=c.config.ranger_user,
                    ranger_password=c.config.ranger_password)),
            content=json.dumps(policy))
        )
