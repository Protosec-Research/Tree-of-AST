import os

class UserInput:
    def __init__(self,input) -> None:
        self.input = input
        
    def __setattr__(self, name, value):
        print(f'[!] {name} now is {value}')
        super().__setattr__(name, value)

def vuln(input=input('Your address: ')):
    user_input = UserInput(input=input).input
    user_input = user_input.split(',') # return a []

    user_input = user_input[3] # user_input's fourth key
    if not 'retr0reg' in user_input: # No 'retr0reg'
        exit()
    user_input = user_input.split('retr0reg')[1] # user_input's third key .split ilovehacking 's first

    print(f'[!] RUNNING {user_input}')
    return os.system(user_input)
    # Payload should be xxx,xxx,xxx,xxxretr0reg<command>

vuln()
