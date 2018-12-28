DOIT_CONFIG = {'check_file_uptodate': 'timestamp_newer',
               'verbosity': 2}

#DOIT_CONFIG = {'check_file_uptodate': 'timestamp',
#               'verbosity': 2}


def task_touch():
    for i in range(1, 7):
        print i
        if i % 2 == 0:
            print i
            yield {
                'file_dep': ['shit.txt'],
                'targets': ['poop_%s.txt' % i],
                'actions': ['touch poop_%s.txt' % (i)],
                'name': 'touch poop %s' % i
                   }
