import logging

PICK_STRATEGY = True
UPDATE_PRICE = True
ARBITRARY_OPINION_INDEX = None

N_STEPS = 30000
N_RUNS = 500
SEED = 42

#simulation parameters 
DT = 0.1
MIN_TRADER = 5
deltap = 0.0001     # price change differential
sloperange = 20     # time-steps used for price slope computation

#market initialization;     fundamental price 
N=500; nt0=450; p0=10;      pf = 10

#excess demand parameters
beta = 6; Tc=2; Tf=1; sigma=10; 

#strategy change parameters
v2=1; a3=.5; r=0.12; R=0.04; s=0.85

#technical opinion parameters
v1=2; a1=0.5; a2=0.8; 

RESULT_DIR = "results/set_1"


#Parameter set I:
# v1=3; v2=2; beta=6; Tc=10; Tf=5; a1=0.6; a2=0.2; a3=0.5; sigma=0.05; s=0.75
# RESULT_DIR = "results/original/parameter_set_1"

# Parameter set II:
# v1=4; v2=1; beta=4; Tc=7.5; Tf=5; a1=0.9; a2=0.25; a3=3; sigma=0.1; s=0.75
# RESULT_DIR = "results/original/parameter_set_2"

# Parameter set III:
# v1=0.5; v2=0.5; beta=2; Tc=10; Tf=10; a1=0.75; a2=0.25; a3=0.75; sigma=0.1; s=0.8
# RESULT_DIR = "results/original/parameter_set_3"

# Parameter set IV: 
# v1=2; v2=0.6; beta=4; Tc=5; Tf=5; a1=0.8; a2=0.2; a3=1; sigma=0.05; s=0.75
# RESULT_DIR = "results/original/parameter_set_4"


nf0 = N - nt0   # number of fundamentalists
tc = Tc/N       # chartist ED weight
gamma = Tf/N    # fundamentalist ED weight

MARKET_LOG_LEVEL = logging.WARN
AGENTI_LOG_LEVEL = logging.WARN