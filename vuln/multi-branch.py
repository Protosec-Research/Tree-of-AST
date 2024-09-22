
# Here's the sink #1
def s1(p1,p2,p3):
    #p1+p2=p3
    eval(p2)

def s1_ce1(p1,p2,p3):
    fs = 'retr0reg'
    s1(fs)

def s1_ce2(p1,p2,p3):
    s1(p1)

def s1_ce2_c1(p1,p2,p3):
    s1_ce2(p1)

def s1_ce2_c2(p1,p2,p3):
    p1 = 'retr0reg'
    s1_ce2(p1)

def c3(p1,p2,p3):
    p1 = input('p1:') 
    s1_ce2_c1(p1)

def main():
    s1_ce1()
    s1_ce2()
    s1_ce2_c1()
    s1_ce2_c2()

if __name__ == '__main__':
    main()