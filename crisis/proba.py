import numpy as np
from sim3 import make_bodies

b = make_bodies(3, np.random.default_rng(1))

print(b["L"])          # [7.25201515 9.18204026 5.6343023 ]
print(b["A_floor"])    # [ 71.03057154 199.63571212  43.34641051]
