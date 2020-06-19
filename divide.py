import random

def div1(a,b):
    '''Takes in two unsigned integers, a, b -> returns an integer a//b
    
    https://www.wikihow.com/Divide-Binary-Numbers
    '''
    
    bitlength = 8
    r = [0 for i in range(4)]
    
    r[0] = a
    r[1] = b
    r[3] = 0
    
    r[1] = r[1] << bitlength - 1
    r[2] = 1 << bitlength - 1
    
    for i in range(bitlength):
        #print(r[0],r[1],r[2],r[3])
        if r[0] >= r[1]:
            r[3] += r[2]
            r[0] += -r[1]
        r[1] = r[1] >> 1
        r[2] = r[2] >> 1
    
    z = r[3]
    return z

def mod1(a,b):
    '''Takes in two unsigned integers, a, b -> returns an integer a mod b
    
    same as div1, just returns a different register
    '''
    
    bitlength = 8
    r = [0 for i in range(4)]
    
    r[0] = a
    r[1] = b
    r[3] = 0
    
    r[1] = r[1] << bitlength - 1
    r[2] = 1 << bitlength - 1
    
    for i in range(bitlength):
        #print(r[0],r[1],r[2],r[3])
        if r[0] >= r[1]:
            r[3] += r[2]
            r[0] += -r[1]
        r[1] = r[1] >> 1
        r[2] = r[2] >> 1
    
    z = r[0]
    return z

if __name__ == "__main__":
    
    print("testing a//b =========================================================================")
    for i in range(100):
        a = random.randint(0,255)
        b = random.randint(1,64)
        z = div1(a,b)
        print(a, b, z, "\t", z == a//b)

    print("testing a mod b ======================================================================")
    for i in range(100):
        a = random.randint(0,255)
        b = random.randint(1,64)
        z = mod1(a,b)
        print(a, b, z, "\t", z == a % b)    
