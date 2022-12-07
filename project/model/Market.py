from __future__ import annotations
from typing import List
from enum import Enum

import logging
import random

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation

from model.Agenti import Trader, log_agent_step
from model.conf import *

logger = logging.getLogger(__name__)
logger.setLevel(MARKET_LOG_LEVEL)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.WARNING)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler(f'Market.log', mode='w')
file_handler.setLevel(MARKET_LOG_LEVEL)
file_handler.setFormatter(formatter)

logger.addHandler(stdout_handler)
logger.addHandler(file_handler)

datacollector_dict = {
    'model_reporters':{
        'tech_optimists': 'tech_optimists',
        'tech_pessimists': 'tech_pessimists',
        'price': 'price',
        'nf': 'nf',
        'technical_fraction': 'technical_fraction',
        'slope': 'slope',
        'opinion_index': 'opinion_index',
        'edt': 'edt',
        'edf': 'edf',
        'ed': 'ed',
        'ept': 'ept',
        'epf': 'epf',
        'p_trans': 'p_trans'
    },
    'agent_reporters': {},
    'tables': {}
}

class Strategy(Enum):
    Tech_O = 1
    Fundam = 0
    Tech_P = -1

class PriceSeries(List[float]):
    def __init__(self, *iterable):
        super().__init__(*iterable)

    def slope(self) -> float:
        if len(self) > sloperange:
            return (self[-1] - self[-sloperange]) / (sloperange * DT)
        return (self[-1] - self[0]) / (len(self) * DT)

class Mercato(Model):
    def __init__(self):
        # Set up model objects
        self.schedule = RandomActivation(self)

        self.nf = nf0
        self.tech_optimists = nt0 // 2
        self.tech_pessimists = nt0 - self.tech_optimists

        self.price = p0
        self.priceseries = PriceSeries([p0])
        self.slope = 0
        self.opinion_index = 0

        self.datacollector = DataCollector(**datacollector_dict)

        self._generate_agents()

        self.running = False

        self._unshceduled_traders = (
            Trader(self, unique_id=-1, strategy=Strategy.Tech_O),
            Trader(self, unique_id=-2, strategy=Strategy.Tech_P),
            Trader(self, unique_id=-3, strategy=Strategy.Fundam)
        )

    def _generate_agents(self):
        for i in range(N):
            strategy = Strategy.Tech_O if i < self.tech_optimists else Strategy.Tech_P if i < nt0 else Strategy.Fundam
            p = Trader(self, unique_id=i, strategy=strategy)
            self.schedule.add(p)

    def start(self):
        self.running = True

    def _update_price(self):
        mu = random.gauss(0, sigma)  # noise term
        U = beta * (self.ed + mu)

        p_trans = abs(U)

        logger.debug(f"EDt: {self.edt:5.4f} - EDf: {self.edf: 5.4f} - ED: {self.ed:5.4f} - noise: {mu:5.4f} - Transition probability: {p_trans:5.3f}")

        if random.random() < p_trans:
            self.price += U * deltap 

    def step(self):
        '''
        Advance the model by one step.
        '''
        logger.info(f"\n\n STEP {self.schedule.steps}\n\n")
        log_agent_step(self.schedule.steps)

        self.slope = self.priceseries.slope()

        logger.debug(f'Excess profits: ept: {self.ept:.4f}  -  epf: {self.epf:.4f}')

        self.schedule.step()

        self.priceseries.append(self.price)
        if UPDATE_PRICE:
            self._update_price()

        self.datacollector.collect(self)
        logger.debug(f"NF: {self.nf:5d} - NT+: {self.tech_optimists:5d} - NT-: {self.tech_pessimists:5d} - Price: {self.price:5.2f}")

    def switch(self, old: Strategy, new: Strategy):
        self.add_to_traders(old, -1)
        self.add_to_traders(new, +1)
        self.opinion_index = ((self.tech_optimists - self.tech_pessimists) / self.nt)

    def get_n_traders(self, strategy: Strategy):
        if strategy == Strategy.Fundam:
            return self.nf
        elif strategy == Strategy.Tech_O:
            return self.tech_optimists
        else:
            return self.tech_pessimists
                    
    def add_to_traders(self, strategy: Strategy, add: int):
        if strategy == Strategy.Fundam:
            self.nf += add
        elif strategy == Strategy.Tech_O:
            self.tech_optimists += add
        else:
            self.tech_pessimists += add

    @property
    def technical_fraction(self):
        return (self.nt) / N

    @property
    def ept(self):
        return (r + self.slope / v2) / self.price - R

    @property
    def epf(self):
        return s * abs((self.price - pf) / self.price)
    
    @property
    def edt(self):
        return (self.tech_optimists - self.tech_pessimists) * tc

    @property
    def edf(self):
        return self.nf * gamma * (pf - self.price)

    @property
    def ed(self):
        return self.edt + self.edf

    @property
    def nt(self):
        return self.tech_optimists + self.tech_pessimists

    @property
    def p_trans(self):
        res = {f'{x.strategy.name}->{s.name}': x.calc_transition_matrix(s) for x in self._unshceduled_traders for s in Strategy if s != x.strategy}
        return res