import os        
def process(a):
    return a.split('love')[1] 

def vuln(input=input('Your address: ')):

    user_input = input
    if 'saveandsound' not in user_input[:11]:
        exit(0)
    else:
        user_input = user_input[7:]
    a = user_input.split(',')
    b = a[3]
    if not 'retr0reg' in b:
        exit()
    c = b
    os.system(c)
    # return os.system(c) # noqa: P204
 
def f1():
    vuln(input='123')
    
def f2():
    vuln()