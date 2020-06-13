'''
Contains multiple algorithms and variations of algorithms for generating prime numbers.

Note: In order to keep all profiling comparisons as 'apples to apples' as possible,
They are all trying to generate all primes less than 1000000
'''

import profile
import sys

#Ommitted for performance reasons
#def isPrime0(t1):
#	"""Takes an integer, returns True if it is a prime number
#	
#	The dumb, simple, and ineffecient way to do it"""
#	assert t1 > 0
#	if t1 == 1:
#		return False
#	for i in range(2, t1):
#		if t1%i == 0:
#			return False
#	return True
#
#print("Profiling isPrime0")
#for i in range(1, 1000000):
#	isPrime0(i)
#profile.run("""
#        for i in range(1, 1000000):
#                isPrime0(i)""")

def isPrime1(t1):
	"""Takes an integer, returns True if it's a prime number
	
	The dumb and simple way to do it"""
	assert t1 > 0
	if t1 == 1:
		return False
	for i in range(2, int(t1**0.5) + 1):
		if t1%i == 0:
			return False
	return True

print("Profiling isPrime1")
for i in range(1, 1000000):
	isPrime1(i)
profile.run("""
for i in range(1, 1000000):
	isPrime1(i)""")

#TODO implement isPrime1, but with 6k+1, 6k+5 number pattern

def isPrime2(): #bad performance since it doesn't stop checking primes > sqrt(i)
	#TODO bad docstring
	"""Takes an integer, returns True if it's a prime number
	
	Assumes every call is a number in sequence, IE: 1,2,3,..."""
	primes = []
	i = 1
	while True:
		if i == None:
			i = (yield False)
			continue
		if i == 1:
			i = (yield False)
			continue
		result = True
		for j in primes:
			if i % j == 0:
				result = False
				break
		if result == True:
			primes.append(i)
			i = (yield True)
		else:
			i = (yield False)

#TODO profile comparison

def isPrime3():
	#TODO bad docstring
	"""Takes an integer, returns True if it's a prime number
	
	Assumes every call is a number in sequence, IE: 1,2,3,..."""
	primes = []
	i = 1
	while True:
		if i == None:
			i = (yield False)
			continue
		if i == 1:
			i = (yield False)
			continue
		result = True
		l = int(i**0.5) + 1
		for j in primes:
			if j > l:
				break
			if i % j == 0:
				result = False
				break
		if result == True:
			primes.append(i)
			i = (yield True)
		else:
			i = (yield False)

print("Profiling isPrime3")
gen = isPrime3()
gen.send(None)
for i in range(1,1000000):
	assert gen.send(i) == isPrime1(i)
gen.close()
profile.run("""
gen = isPrime3()
gen.send(None)
for i in range(1,1000000):
	gen.send(i)
gen.close()""")
print("isPrime2 sanity check passed ============================================")

def primeGenerator1(limit=100):
	primes = [2,3,5]
	i = 5
	t = 4
	yield 2
	yield 3
	yield 5
	while i < limit:
		t = 2 + (t % 4) #generates number pattern of 6k+1,6k+5, k>=1
		i += t
		isPrime = True
		z = int(i**0.5) + 1
		for j in primes:
			if j > z:
				break
			if i % j == 0:
				isPrime = False
				break
		if isPrime == True:
			primes.append(i)
			yield i

print("Profiling primeGenerator1")
i = 0
primes = [i for i in range(1, 1000000) if isPrime1(i)]
for j in primeGenerator1(1000000):
	assert j == primes[i]
	i += 1
profile.run("""
for j in primeGenerator1(1000000):
	pass""")
print("primeGenerator1 sanity check passed =====================================")

#generates base list to sanity check other methods
print("Profiling [i for i in range(1, 1000000) if isPrime1(i)]")
primes = [i for i in range(1, 1000000) if isPrime1(i)]
profile.run("t = [i for i in range(1, 1000000) if isPrime1(i)]")

#ommitted for performance reasons
#print("Profiling [i for i in range(2,100000) if not [j for j in range(2,i) if not (i % j)]]")
#primes2 = [i for i in range(2,100000) if not [j for j in range(2,i) if not (i % j)]] # Original found on internet https://stackoverflow.com/questions/567222/simple-prime-generator-in-python
#for i in range(len(primes)):
#	assert primes[i] == primes2[i]
#profile.run("[i for i in range(2,100000) if not [j for j in range(2,i) if not (i % j)]]")

print("Profiling [i for i in range(2, 1000000) if 0 == sum([j for j in range(2,int(i**0.5)+1) if (0 == i%j)])]")
primes3 = [i for i in range(2, 1000000) if 0 == sum([j for j in range(2,int(i**0.5)+1) if (0 == i%j)])]
for i in range(len(primes)):
	assert primes[i] == primes3[i]
profile.run("[i for i in range(2,1000000) if 0 == sum([j for j in range(2,int(i**0.5)+1) if (0 == i%j)])]")

print("Profiling [i for i in [2,3,5]+[h for h in range(7,1000000,2)] if 0 == sum([j for j in range(2,int(i**0.5)+1) if (0 == i%j)])]")
primes4 = [i for i in [2,3,5]+[h for h in range(7,1000000,2)] if 0 == sum([j for j in range(2,int(i**0.5)+1) if (0 == i%j)])]
for i in range(len(primes)):
	assert primes[i] == primes4[i]
profile.run("[i for i in [2,3,5]+[h for h in range(7,1000000,2)] if 0 == sum([j for j in range(2,int(i**0.5)+1) if (0 == i%j)])]")

print("prime list comprehension sanity check passed ============================")

def sieveOfEratosthenes1(limit=10000):
	"""Tales an optional intager limit, returns a list of prime numbers up to that limit
	
	uses the pseudocode from https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes#Pseudocode
	"""
	elements = [True for i in range(limit)]
	elements[0] = False #corrisponds to the number 0
	elements[1] = False #corrisponds to the number 1
	for i in range(2, int(limit**0.5) + 1):
		if elements[i] == True:
			#marks as not prime i**2, i**2+i, i**2+2*i, i**2+3*i, ...
			j = i**2
			while j < limit:
				elements[j] = False
				j += i
	
	primes = []
	for i in range(limit):
		if elements[i] == True:
			primes.append(i)
	
	return primes

print("Profiling sieveOfEratosthenes1")
primes = [i for i in range(1, 1000000) if isPrime1(i)]
primesSieve = sieveOfEratosthenes1(1000000)
for i in range(len(primes)):
	assert primes[i] == primesSieve[i]
profile.run("sieveOfEratosthenes1(1000000)")
print("sieveOfEratosthenes1 sanity check passed ================================")

#===================================================================================================================================
print("Experimental Stuff Here =================================================")

def lowpassIterator1(maxElements=2, limit=10000):
	"""A prime number generator (unoptimized, for readability and testing)
	
	maxElements is the max size of the array that can be generated for the iterator (IE: the lowpass filter)(IE: a reverse sieve of Eratosthenes)
	
	experimental and may have issues
	"""
	'''
	potential primes/total numbers	savings in terms of numbers that need to be checked
	1/2				0.5
	2/6				0.33333333333
	8/30				0.26666666666
	48/210				0.22857142857
	480/2310			0.20779220779
	5760/30030			0.1918081918
	92160/510510			0.18052535699
	1658880/9699690			0.17102402241
	36495360/223092870		0.16358819535
	'''	
	assert maxElements >= 2
	
	iterator = []
	start = 0
	primes = [2,3]
	while len(iterator) < maxElements:
		lowerBound = 1
		
		for i in primes:
			lowerBound = lowerBound*i
			
		numberSieve = [] #generates a range of numbers that are not dividable by numbers in primes variable
		for i in range(lowerBound, lowerBound*2):
			shouldAdd = True
			for j in primes:
				if i%j == 0:
					shouldAdd = False
					break
			if shouldAdd == True:
				numberSieve.append(i)
		
		iteratorRaw = [] 
		for i in numberSieve:
			iteratorRaw.append(i - lowerBound)	
		offset = lowerBound - iteratorRaw[-1]
		print("offset", offset)
		
		for i in range(0, len(iteratorRaw)):
			iteratorRaw[i] = iteratorRaw[i] + offset
		iteratorRaw.insert(0,0)
		
		newIterator = []
		for i in range(0, len(iteratorRaw) - 1):
			newIterator.append(iteratorRaw[i+1] - iteratorRaw[i])

		print("start: ", lowerBound - (lowerBound*2 - numberSieve[-1]))
		print("element length: ", len(newIterator))
		print("max of elements: ", max(newIterator))
		print("range: ", lowerBound)		
		print("")
		
		if len(newIterator) >= maxElements:
			start = lowerBound - (lowerBound*2 - numberSieve[-1])
			iterator = newIterator
			break
				
		j = primes[-1]
		while True:
			j += 1
			if isPrime1(j):
				primes.append(j)
				break
	
	for i in range(1, start):
		if i > limit:
			break
		if isPrime1(i):
			yield i
	
	i = start
	j = 0
	while i <= limit:
		if isPrime1(i):
			yield i
		i = i + iterator[j]
		j = (j + 1) % len(iterator)

i = 0
primes = [i for i in range(1, 1000000) if isPrime1(i)]
for j in lowpassIterator1(1000, 1000000):
	assert j == primes[i]
	i += 1
profile.run("""for j in lowpassIterator1(1000, 1000000):
	pass""")
print("lowpassIterator1 sanity check passed ====================================")

def lowpassIterator2(maxElements=2, limit=10000):
	"""A prime number generator (unoptimized, for readability and testing)
	
	maxElements is the max size of the array that can be generated for the iterator (IE: the lowpass filter)(IE: a reverse sieve of Eratosthenes)
	
	experimental and may have issues
	"""
	assert maxElements >= 2
	
	iterator = ()
	start = 0
	primes = [2,3]
	while len(iterator) < maxElements:
		lowerBound = 1	
		for i in primes:
			lowerBound = lowerBound*i
			
		numberSieve = [] #generates a range of numbers that are not dividable by numbers in primes variable
		for i in range(lowerBound, lowerBound*2):
			shouldAdd = True
			for j in primes:
				if i%j == 0:
					shouldAdd = False
					break
			if shouldAdd == True:
				numberSieve.append(i)
		
		offset = lowerBound*2 - numberSieve[-1]
		high = numberSieve[-1]
		
		print("offset: ", offset)
		print("start: ", high - lowerBound)
		
		iteratorRaw = tuple([0]+[i - lowerBound + offset for i in numberSieve])
		newIterator = tuple([iteratorRaw[i+1] - iteratorRaw[i] for i in range(0, len(iteratorRaw) - 1)])
		
		print("element length: ", len(newIterator))
		print("max of elements: ", max(newIterator))
		print("range: ", lowerBound)
		print("")
		
		if len(newIterator) >= maxElements:
			start = high - lowerBound
			iterator = newIterator
			break
				
		j = primes[-1]
		while True:
			j += 1
			if isPrime1(j):
				primes.append(j)
				break
	
	for i in range(1, start):
		if i > limit:
			break
		if isPrime1(i):
			yield i
	
	i = start #TODO: start should return number corrisponding to iterator[1] as can't garuentee number less then that is not prime, at least for initial initialization (IE: numbers < primes[0]*primes[1]*primes[2]*...)
	j = 0 #TODO: should be 1 as per the above comment
	l = len(iterator)
	
	#this part is where it starts returning output
	while i <= limit:
		if isPrime1(i):
			yield i
		i = i + iterator[j]
		j = (j + 1) % l


i = 0
primes = [i for i in range(1, 1000000) if isPrime1(i)]
for j in lowpassIterator2(1000, 1000000):
	assert j == primes[i]
	i += 1
	
profile.run("""for j in lowpassIterator2(1000, 1000000):
	pass""")
	
print("lowpassIterator2 sanity check passed ====================================")
