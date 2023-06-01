#!/usr/local/bin/Rscript

nterms = 10
# first two terms                                                               
n1 = 0
n2 = 1
count = 2
print("Fibonacci sequence:")
print(n1)
print(n2)
while(count < nterms) {
    nth = n1 + n2
    print(nth)
    # update values                                                         
    n1 = n2
    n2 = nth
    count = count + 1
}

