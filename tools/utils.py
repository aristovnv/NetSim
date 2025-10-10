import numpy as np

# ---------------------------
# Demand / supply generator
# ---------------------------

def sample_distribution(spec, rng):
    dist = spec.get("dist", "normal")
    if dist == "normal":
        return max(0.0, rng.gauss(spec.get("mu", 0.0), spec.get("sigma", 1.0)))
    elif dist == "uniform":
        return rng.uniform(spec.get("low", 0.0), spec.get("high", 1.0))
    elif dist == "poisson":
        return float(np.random.poisson(spec.get("lam", 1.0)))
    else:
        return rng.random()