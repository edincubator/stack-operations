import base64
import json

import requests

import invoke
from fabric.connection import Connection
from mockito import unstub, verify, when
from operations import ranger


class MockedResponse(object):
    def json(self):
        response = {'policyItems': [{'users': []}]}
        return response


class TestRanger(object):
    def test_update_ranger_usersync(self):
        c = Connection('root')

        when(c).run(
          '/usr/jdk64/jdk1.8.0_112/bin/java -Dlogdir=/var/log/ranger/usersync '
          '-cp "/usr/hdp/current/ranger-usersync/dist/'
          'unixusersync-0.7.0.2.6.5.0-292.jar:/usr/hdp/current/ranger-usersync'
          '/dist/ranger-usersync-1.0-SNAPSHOT.jar:/usr/hdp/current/'
          'ranger-usersync/lib/*:/etc/ranger/usersync/conf" '
          'org.apache.ranger.usergroupsync.UserGroupSyncTrigger')

        ranger.update_ranger_usersync(c)

        verify(c).run(
          '/usr/jdk64/jdk1.8.0_112/bin/java -Dlogdir=/var/log/ranger/usersync '
          '-cp "/usr/hdp/current/ranger-usersync/dist/'
          'unixusersync-0.7.0.2.6.5.0-292.jar:/usr/hdp/current/ranger-usersync'
          '/dist/ranger-usersync-1.0-SNAPSHOT.jar:/usr/hdp/current/'
          'ranger-usersync/lib/*:/etc/ranger/usersync/conf" '
          'org.apache.ranger.usergroupsync.UserGroupSyncTrigger')

        unstub()

    def test_create_ranger_policy(self):
        username = 'username'
        resource = '/my/path'
        policy_name = 'my_policy_name'
        policy_description = 'This is a test policy'
        resource_type = 'path'
        service = 'hadoop'

        c = Connection('root')
        c.config.ranger_url = 'http://ranger.url'
        c.config.ranger_user = 'rangeruser'
        c.config.ranger_password = 'rangerpassword'
        c.config.ranger_cluster_name = 'my_cluster'

        template = json.load(
            open('ranger_templates/{}.json'.format(service), 'r'))
        template['service'] = '{cluster_name}_{service}'.format(
            cluster_name=c.config.ranger_cluster_name, service=service)
        template['name'] = policy_name
        template['description'] = policy_description
        template['resources'][resource_type]['values'].extend(resource)
        template['policyItems'][0]['users'].append(username)

        when(invoke).run(
            "curl -X POST {ranger_url}/service/public/v2/api/policy "
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

        ranger.create_ranger_policy(
            c, resource, username, policy_name,
            policy_description, resource_type, service)

        verify(invoke).run(
            "curl -X POST {ranger_url}/service/public/v2/api/policy "
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

        unstub()

    def test_update_nifi_flow_ranger_policy(self):
        username = 'username'

        c = Connection('root')
        c.config.ranger_url = 'http://rager.url'
        c.config.nifi_ranger_flow_policy_id = 10
        c.config.ranger_user = 'rangeruser'
        c.config.ranger_password = 'rangerpassword'

        response = MockedResponse()

        when(requests).get(
            '{ranger_url}/service/public/v2/api/policy/{policy_id}'.format(
                ranger_url=c.config.ranger_url,
                policy_id=c.config.nifi_ranger_flow_policy_id),
            headers={'content-type': 'application/json'},
            auth=(c.config.ranger_user, c.config.ranger_password),
            verify=False
        ).thenReturn(response)

        policy = response.json()
        policy['policyItems'][0]['users'].append(username)

        when(invoke).run(
          "curl -X PUT {ranger_url}/service/public/v2/api/policy/{policy_id} "
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

        ranger.update_nifi_flow_ranger_policy(c, username)

        verify(requests).get(
            '{ranger_url}/service/public/v2/api/policy/{policy_id}'.format(
                ranger_url=c.config.ranger_url,
                policy_id=c.config.nifi_ranger_flow_policy_id),
            headers={'content-type': 'application/json'},
            auth=(c.config.ranger_user, c.config.ranger_password),
            verify=False
        )

        verify(invoke).run(
          "curl -X PUT {ranger_url}/service/public/v2/api/policy/{policy_id} "
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

        unstub()
