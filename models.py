from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
)

import csv
import decimal
import random

def call_market(market_bids, market_asks):
    qstar = 0
    price = 0

    # sort the lists of variables
    market_bids_sorted = list(sorted(market_bids, reverse=True))
    market_asks_sorted = list(sorted(market_asks))
    i = 0

    while market_bids_sorted[i] >= market_asks_sorted[i]:
        qstar = i + 1
        i += 1
        if i == len(market_bids_sorted) or i == len(
                market_asks_sorted):  # note we break the loop if we are at the end of the list
            break

    # Compute market prices. we extend lists just in case we are at the end of the lists...
    market_asks_sorted.extend([10000])
    market_bids_sorted.extend([-10])
    price = (min(market_asks_sorted[i], market_bids_sorted[i - 1]) + max(market_bids_sorted[i],
                                                                         market_asks_sorted[i - 1])) / 2

    return qstar, price

class Constants(BaseConstants):
    name_in_url = 'voting'
    players_per_group = None
    instructions_template = 'voting/instructions.html'
    num_rounds = 100
    upper_n = 11

def parse_config(config_file):
    with open('voting/configs/' + config_file) as f:
        rows = list(csv.DictReader(f))

    rounds = []
    for row in rows:
        rounds.append({
            'round_number': int(row['round']),
            'uniforme': True if row['uniforme'] == 'TRUE' else False,
            'cash': c(row['cash']),
            'v': c(row['v']),
            'endowment': int(row['endowment']),
            'subperiods': int(row['subperiods']),
            'h': c(row['h']),
            'tau': c(row['tau']),
            'pay_round': int(row['pay_round']),
            'players_per_group': int(row['players_per_group']),
            'voting_stage': True if row['voting_stage'] == 'TRUE' else False,
            'cambio': int(row['cambio'])

        })
    return rounds

class Subsession(BaseSubsession):

    def num_rounds(self):
        return len(parse_config(self.session.config['config_file']))

    def players_per_group(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['players_per_group']

    def uniforme(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['uniforme']

    def cash(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['cash']

    def endowment(self):
        return parse_config(self.session.config['config_file'])[self.round_number - 1]['endowment']

    def v(self):
        return parse_config(self.session.config['config_file'])[self.round_number - 1]['v']

    def h(self):
        return parse_config(self.session.config['config_file'])[self.round_number - 1]['h']

    def tau(self):
        return parse_config(self.session.config['config_file'])[self.round_number - 1]['tau']

    def pay_round(self):
        return parse_config(self.session.config['config_file'])[self.round_number - 1]['pay_round']

    def voting_stage(self):
        return parse_config(self.session.config['config_file'])[self.round_number - 1]['voting_stage']

    def cambio(self):
        return parse_config(self.session.config['config_file'])[self.round_number - 1]['cambio']

    def subperiods(self):
        return parse_config(self.session.config['config_file'])[self.round_number - 1]['subperiods']

    def do_grouping(self):
        ppg = self.config['players_per_group']
        # if ppg is None, just use the default grouping where everyone is in one group
        if not ppg:
            return
        group_matrix = []
        players = self.get_players()
        for i in range(0, len(players), ppg):
            group_matrix.append(players[i:i + ppg])
        self.set_group_matrix(group_matrix)

    def creating_session(self):
        config = self.config
        if not config:
            return

        self.do_grouping()
        if self.round_number <= self.cambio():
            if self.uniforme():
                for p in self.get_players():
                    p.lama = (p.id_in_group-1)/Constants.upper_n
            else:
                for p in self.get_players():
                    p.lama = 0
                    if p.id_in_group<6:
                        p.lama = 1
        else:
            dict = {1: 11, 2: 10, 3: 9, 4: 8, 5: 7, 6: 4, 7: 5, 8: 6, 9: 3, 10: 2, 11: 1}
            if self.uniforme():
                for p in self.get_players():
                    p.lama = (dict[p.id_in_group] - 1) / Constants.upper_n
            else:
                for p in self.get_players():
                    p.lama = 1
                    if p.id_in_group < 7:
                        p.lama = 0
    @property
    def config(self):
        try:
            return parse_config(self.session.config['config_file'])[self.round_number - 1]
        except IndexError:
            return None


class Group(BaseGroup):
    price = models.DecimalField(max_digits=5, decimal_places=2)
    q = models.IntegerField()
    policy = models.IntegerField()
    costo = models.IntegerField()
    uniforme = models.BooleanField()

    def clearing_market(self):
        self.q = 0
        self.price = 0

        # Create lists of variables: asks and bids per unit with their player id
        market_bids = []
        market_bids_random = []
        market_asks = []
        market_asks_random = []
        list_buyers = []
        list_sellers = []

        players = self.get_players()

        for p in players:
            p.t = 0
            p.ask = p.bid
            if p.bid > 0:
                market_bids.extend([p.bid])
                market_bids_random.extend(
                    [decimal.Decimal(p.bid) + decimal.Decimal(random.random() / 100000.0)])
                list_buyers.extend([p])

            if p.ask > 0:
                market_asks.extend([p.ask])
                market_asks_random.extend(
                    [decimal.Decimal(p.ask) + decimal.Decimal(random.random() / 100000.0)])
                list_sellers.extend([p])

        if max(market_bids or [-10]) >= min(market_asks or [10000000]):
            self.q, self.price = call_market(market_bids, market_asks)

            buyers_sorted = sorted(zip(market_bids_random, list_buyers), reverse=True)
            (market_bids_sorted, list_buyers_sorted) = zip(*buyers_sorted)
            final_list_buyers = list(list_buyers_sorted)[:(self.q)]

            sellers_sorted = sorted(zip(market_asks_random, list_sellers))
            (market_asks_sorted, list_sellers_sorted) = zip(*sellers_sorted)
            final_list_sellers = list(list_sellers_sorted)[:(self.q)]

            for p in final_list_buyers:
                p.t += 1

            for p in final_list_sellers:
                p.t -= 1


    def set_payoffs(self):
        players = self.get_players()

        for p in players:

            if self.subsession.voting_stage() == False:
                marca = float((self.subsession.endowment()+p.t)*self.subsession.tau())/float(self.subsession.h())
                print(marca)

                if self.subsession.endowment()+p.t > 0 and p.lama >= marca:
                    p.vote = 1
                else:
                    p.vote = 0

            if self.subsession.endowment()+p.t == 0:
                p.vote = 0


        if sum([p.vote*(self.subsession.endowment()+p.t) for p in self.get_players()]) >= (self.subsession.players_per_group()+1)/2:
            self.policy = 1
        else:
            self.policy = 0

        for p in players:
            p.payoff = self.subsession.endowment()*self.subsession.v() + p.t*(self.subsession.v()- self.price) + self.policy*(p.lama*self.subsession.h()-(self.subsession.endowment()+p.t)*self.subsession.tau())
            if self.subsession.round_number != self.subsession.pay_round():
                p.participant.payoff -= p.payoff

        self.uniforme = self.subsession.uniforme()
        self.costo = int(self.subsession.tau())

class Player(BasePlayer):

    t = models.IntegerField()
    vote = models.IntegerField(
        choices=[
            [0, 'Reject the policy'],
            [1, 'Accept the policy'],
        ],
        default=None,
        widget=widgets.RadioSelect
    )

    bid = models.DecimalField(max_digits=8, decimal_places=2, label="",min=0)#max= self.subsession.cash)
    ask = models.DecimalField(max_digits=8, decimal_places=2, label="", min=0)#,max=self.subsession.cash)
    lama = models.DecimalField(max_digits=8, decimal_places=2, label="",min=0)