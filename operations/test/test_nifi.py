from fabric.connection import Connection
from mockito import unstub, verify, when
from operations import nifi, ranger


class TestNifi(object):
    def test_grant_processgroup(self):
        username = 'username'
        process_group_id = 1

        c = Connection('root')

        when(ranger).create_ranger_policy(
            c,
            ['/process-groups/{id}'.format(id=process_group_id),
             '/data/process-groups/{id}'.format(id=process_group_id)],
            username,
            'Process group {id}'.format(id=process_group_id),
            'Policy for NiFi process group {id}'.format(id=process_group_id),
            'nifi-resource',
            'nifi'
        )

        nifi.grant_processgroup(c, process_group_id, username)

        verify(ranger).create_ranger_policy(
            c,
            ['/process-groups/{id}'.format(id=process_group_id),
             '/data/process-groups/{id}'.format(id=process_group_id)],
            username,
            'Process group {id}'.format(id=process_group_id),
            'Policy for NiFi process group {id}'.format(id=process_group_id),
            'nifi-resource',
            'nifi'
        )

        unstub()
