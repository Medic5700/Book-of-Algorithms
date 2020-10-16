'''
Author: Medic5700

'''

scaleFactor = 20 #computes with a resolution of 1/20 = 0.05
mandelbrotSet = [[False for y in range((1*scaleFactor)*2+1)] for x in range((2*scaleFactor)*2+1)]

for x in range(-2*scaleFactor, 2*scaleFactor):
    for y in range(-1*scaleFactor, 1*scaleFactor):
        cx = x/scaleFactor
        cy = y/scaleFactor
        
        zx = 0
        zy = 0
        
        i = 0
        while True:
            '''
            z_(n+1) = z_n^2 + c
            if z remains bounded for a given c, then c is in the set
            z and c are complex numbers
            
            z = z^2 + c
            (a+b*i) = (a+b*i)^2 + (c_1+c_2*i)
            (a+b*i) = (a+b*i)(a+b*i) + (c_1+c_2*i)
            (a+b*i) = (a^2 + a*b*i + b*i*a + b*i^2) + (c_1+c_2*i)
            (a+b*i) = (a^2 + 2*a*b*i + b^2*i^2) + (c_1+c_2*i)
            (a+b*i) = (a^2 + 2*a*b*i + b^2*(-1)) + (c_1+c_2*i)
            (a+b*i) = (a^2 + 2*a*b*i - b^2) + (c_1+c_2*i)
            (a+b*i) = a^2 - b^2 + c_1 + 2*a*b*i + c_2*i
            break it into real and imaginary components
            (real, imaginary) = (a^2 - b^2 + c_1, 2*a*b*i + c_2*i)
            '''
            #(x+y)(x+y) = (x^2 + xy + yx + y^2) = (x^2 + 2xy + y^2)
            zx0 = zx**2 - zy**2 + cx
            zy0 = 2*zx*zy + cy
            if zx0**2 + zy0**2 > 2**2:
                break
            if zx0**2 + zy0**2 < 2**2 and i > 100:
                mandelbrotSet[x][y] = True
            if i > 100:
                break
            zx = zx0
            zy = zy0
            i += 1


for y in range(20, -20, -2): #prints every other line since characters in the terminal are rectangles, not square pixels
    test = ""
    for x in range(-40, 40):
        if mandelbrotSet[x][y] == True:
            test += "8"
        else:
            test += " "
    print(test)



