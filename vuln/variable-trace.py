import os

class UserInput:
   def __init__(self,input) -> None:
       self.input = input
       
   def __setattr__(self, name, value):
       print(f'[!] {name} now is {value}')
       super().__setattr__(name, value)

def vuln(input=input('Your address: ')):
   # ANALYSIS-TOP: [<arbitrary>, <arbitrary>, <arbitrary>retr0reglove<COMMAND>]

   user_input = UserInput(input=input).input

   # ANALYSIS: tytytyty<arbitrary>, <arbitrary>, <arbitrary>retr0reglove<COMMAND>

   if 'tytytyty' not in user_input[:7]:
       exit(0)
   else:
       user_input = user_input[7:]

   # ANALYSIS: <arbitrary>, <arbitrary>, <arbitrary>retr0reglove<COMMAND>
   user_input = user_input.split(',')

   # ANALYSIS UNSURE TYPE, lookahead simulations
   # ANALYSIS: [<arbitrary>, <arbitrary>, <arbitrary>retr0reglove<COMMAND>]
   user_input = user_input[3]
   
   # ANALYSIS: <arbitrary>retr0reglove<COMMAND>,
   #           retr0reg<arbitrary>love<COMMAND>
   if not 'retr0reg' in user_input:
       exit()

   user_input = user_input.split('love')[1] 
   
   return os.system(user_input)

vuln()
