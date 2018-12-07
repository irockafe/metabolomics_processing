import os
import yaml
# Goal of this is to define the user-specific things
# Specifically:
# The cloud_provider, bucket_path

# Ask about cloud provider
cloud = raw_input('\nAre you working in a cloud? (y/n)')
if cloud == 'y':
    provider = raw_input('\nAmazon or google? (type amazon or google)')
    if provider.lower() not in ['amazon', 'google']:
        raise ValueError('you should have typed amazon or google')
    bucket = raw_input('\nWhat is the path to your storage bucket?')
elif cloud == 'n':
    provider = 'none'
    bucket='none'
    print('\n\n' + '''NOTE This code was only tested using cloud buckets.
    I haven't tested this at all. You'll have to add a Volume to the
    docker-compose.yml and possibly debug some stuff\n
    If you're not okay with that, re-run src/get_user_info.py or
    edit user_input/user_settings.yml''')
else:
    raise ValueError('should have typed y or n')

output = {'cloud_provider': provider, 'storage': bucket}
yaml.dump(output, file('/home/user_input/user_settings.yml', 'w'),
        default_flow_style=False)

