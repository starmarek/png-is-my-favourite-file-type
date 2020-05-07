import math, random

class KeyGenerator:
    def __init__(self, keysize):
        self.keysize=keysize

    def isPrime(self, num):
        # Returns True if num is a prime number.
        if num % 2 == 0 or num < 2:
            return False # Rabin-Miller doesn't work on even integers.
        if num == 3:
            return True
        s = num - 1
        t = 0
        while s % 2 == 0:
        # Keep halving s until it is odd (and use t
        # to count how many times we halve s):
            s = s // 2
            t += 1
        for trials in range(5): # Try to falsify num's primality 5 times.
            a = random.randrange(2, num - 1)
            v = pow(a, s, num)
            if v != 1: # This test does not apply if v is 1.
                 i = 0
                 while v != (num - 1):
                    if i == t - 1:
                        return False
                    else:
                        i = i + 1
                        v = (v ** 2) % num
        return True

    def egcd(self, a, b):
        if a == 0:
            return (b, 0, 1)
        g, y, x = self.egcd(b%a,a)
        return (g, x - (b//a) * y, y)

    def modinv(self, a, m):
        g, x, y = self.egcd(a, m)
        if g != 1:
            raise Exception('No modular inverse')
        return x%m

    def generateLargePrime(self):
        while True:
            num = random.randrange(2**(self.keysize-1), 2**(self.keysize))
            if self.isPrime(num):
                return num
    
    def gcd(self, a, b): #gcd - najwiekszy wspolny dzielnik(greatest common divisor)
        if b==0: 
            return a 
        else: 
            return self.gcd(b,a%b) 

    
    def generateKeys(self):
        p = 0
        q = 0
        # Step 1: Create two prime numbers, p and q. Calculate n = p * q:
        while p == q:
            p = self.generateLargePrime()
            q = self.generateLargePrime()
        n = p * q
        phi = (p-1)*(q-1)
        
        while True:
        # Keep trying random numbers for e until one is valid:
            e = random.randrange(2 ** (self.keysize - 1), 2 ** (self.keysize))
            if self.gcd(e, phi) == 1:
                break
        
        d = self.modinv(e, phi)
        publicKey=(e,n)
        privateKey=(d,n)
        return (publicKey, privateKey)


#TESTS
#x = KeyGenerator(1024)
#y=x.generateLargePrime()
#print(y)
#print(x.isPrime(y))
#print(x.generateKeys())