DOIT_CONFIG = {'check_file_uptodate': 'timestamp_newer',
               'verbosity': 2}


def task_touch():
    for i in range(1,7):
        print i
        if i % 2 == 0:
            print i
            yield {
                'targets': ['poop_%s.txt' % i],
                'file_dep': ['shit.txt'],
                'actions': ['touch poop_%s.txt feces_%s.txt' % (i,i)],
                'name': 'touch poop feces %s' % i
                   }
