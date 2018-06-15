import ranger
from invoke import task


@task(help={
    'process_group_id': 'ID of the NiFi process group',
    'username': 'User to be granted for writing editing the process group'})
def grant_processgroup(c, process_group_id, username):
    """
    Grants a user with read and write permissions for a NiFi process group.
    """
    ranger.create_ranger_policy(
        ['/process-groups/{id}'.format(id=process_group_id),
         '/data/{id}'.format(id=process_group_id)],
        username,
        'Process group {id}'.format(id=process_group_id),
        'Policy for NiFi process group {id}'.format(id=process_group_id),
        'nifi-resource',
        'nifi'
    )
