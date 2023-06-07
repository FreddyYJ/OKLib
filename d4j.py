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
    'Closure_5',
    'Closure_8',
    'Closure_10',
    'Closure_13',
    'Closure_15',
    'Closure_20',
    'Closure_51',
    'Closure_52',
    'Closure_57',
    'Closure_62',
    'Closure_66',
    'Closure_67',
    'Closure_70',
    'Closure_73',
    'Closure_92',
    'Closure_97',
    'Closure_102',
    'Closure_104',
    'Closure_118',
    'Closure_124',
    'Closure_129',
    'Closure_133',
    'Lang_3',
    'Lang_6',
    'Lang_16',
    'Lang_21',
    'Lang_24',
    'Lang_26',
    'Lang_29',
    'Lang_38',
    'Lang_53',
    'Math_5',
    'Math_11',
    'Math_22',
    'Math_27',
    'Math_30',
    'Math_46',
    'Math_57',
    'Math_59',
    'Math_80',
    'Math_82',
    'Maht_94',
    'Mockito_26',
    'Time_4',
    'Time_16',
    'Time_19',
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