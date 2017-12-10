DOIT_CONFIG = {'check_file_uptodate': 'timestamp',
                              'verbosity': 2}

def task_touch():
    yield {
        'targets': ['poop.txt'],
        'file_dep': ['shit.txt'],
        'actions': ['touch poop.txt feces.txt'],
        'name': 'touch poop feces'
    }
