def montecarlopiapprox_single(n):
    """
    Monte Carlo approximation of pi. Single-threaded implementation
    From: Advanced Python Programming, Lanaro
    """
    import random

    samples = int(n)
    hits = 0

    for i in range(samples):
        x = random.uniform(-1., 1.)
        y = random.uniform(-1., 1.)

        if(x**2 + y**2) <= 1:
            hits += 1

    pi = 4.0 * hits/samples
    return(pi)


# Pi approximation of pi via Monte-Carlo method, multi-threaded implementation
def montecarlopiapprox_multi(n):
    import random
    import multiprocessing

    def sample():
        x = random.uniform(-1., 1.)
        y = random.uniform(-1., 1.)
        if (x**2 + y**2) <= 1:
            return(1)
        else:
            return(0)

    pool = multiprocessing.Pool()
    results_async = [pool.apply_async(sample) for i in range(int(n))]
    hits = sum(r.get() for r in results_async)

    pi = 4.0 * hits/int(n)

    return(pi)





if(__name__ == '__main__'):
    pi = montecarlopiapprox_single(1E7)
    #pi = montecarlopiapprox_multi(1E4)
    print(pi)

    exit(0)