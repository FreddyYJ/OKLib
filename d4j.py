import subprocess

D4J_PROJECTS=(
    'Chart-1',
    'Chart-3',
    'Chart-7',
    'Chart-8',
    'Chart-10',
    'Chart-11',
    'Chart-12',
    'Chart-20',
    'Closure-5',
    'Closure-8',
    'Closure-10',
    'Closure-13',
    'Closure-15',
    'Closure-20',
    'Closure-51',
    'Closure-52',
    'Closure-57',
    'Closure-62',
    'Closure-66',
    'Closure-67',
    'Closure-70',
    'Closure-73',
    'Closure-92',
    'Closure-97',
    'Closure-102',
    'Closure-104',
    'Closure-118',
    'Closure-124',
    'Closure-129',
    'Closure-133',
    'Lang-3',
    'Lang-6',
    'Lang-16',
    'Lang-21',
    'Lang-24',
    'Lang-26',
    'Lang-29',
    'Lang-38',
    'Lang-53',
    'Math-5',
    'Math-11',
    'Math-22',
    'Math-27',
    'Math-30',
    'Math-46',
    'Math-57',
    'Math-59',
    'Math-80',
    'Math-82',
    'Maht-94',
    'Mockito-26',
    'Time-4',
    'Time-16',
    'Time-19',
)

def run(project:str):
    print(f'Running {project}...')
    result=subprocess.run(['python3','run.py',project],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

    with open(f'd4j_logs/{project}.log','w') as f:
        f.write(result.stdout.decode('utf-8'))

    print(f'Finished {project}!')

if __name__=='__main__':
    for project in D4J_PROJECTS:
        run(project)