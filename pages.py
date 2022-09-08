from ._builtin import Page, WaitPage
from otree.api import Currency as c, currency_range
from .models import Constants
from .models import parse_config


class Introduction(Page):
    def is_displayed(self):
        return self.round_number == 1
    """Description of the game: How to play and returns expected"""

    pass

class News(Page):
    def is_displayed(self):
        return self.round_number % (self.subsession.subperiods()+1) == 0 or self.round_number == 1
    """Description of the game: How to play and returns expected"""

    pass
    """Description of the game: How to play and returns expected"""
    pass

    def vars_for_template(self):
        me = self.player
        return dict(
            tau= int(self.subsession.tau()),
            private_benefit= int(me.lama*self.subsession.h()),
            subperiods = self.subsession.subperiods(),
        )



class Market(Page):
    """Player: Choose how much to bid / ask"""
    def is_displayed(self):
        return self.subsession.config is not None

    form_model = 'player'
    form_fields = ['bid']

    def error_message(self, value):
        if value["bid"] > self.subsession.cash():
            return 'Please enter a value lower than the initial cash'


    def vars_for_template(self):
        me = self.player
        return dict(
            cash = self.subsession.cash(),
            endowment= self.subsession.endowment(),
            tau= self.subsession.tau(),
            my_lama = me.lama,
            private_benefit= int(me.lama*self.subsession.h()),
            net_private_benefit= int(self.subsession.v() + me.lama * self.subsession.h() - self.subsession.tau()),
            value_2= int(self.subsession.v()*2),
            value_1 = int(self.subsession.v()),
            net_private_benefit_2= int(self.subsession.v()*2 + me.lama * self.subsession.h() - self.subsession.tau()*2),
        )


class ResultsWaitPage1(WaitPage):

    def is_displayed(self):
        return self.subsession.config is not None

    after_all_players_arrive = 'clearing_market'

    body_text = "Waiting for other participants to submit their choices."

class Voting(Page):
    def is_displayed(self):
        if self.subsession.config is not None:
            if self.subsession.voting_stage() == True:
                return self.player.t >= 0
            else:
                return self.subsession.voting_stage() == True
        else:
            return self.subsession.config is not None

    form_model = 'player'
    form_fields = ['vote']

    def vars_for_template(self):
        me = self.player
        return dict(
            endowment= self.subsession.endowment(),
            tau= int(self.subsession.tau()),
            my_lama = me.lama,
            private_benefit= int(me.lama*self.subsession.h()),
            value_asset= int(self.subsession.v()*(me.t + self.subsession.endowment())),
            net_private_benefit= int(self.subsession.v()*(me.t + self.subsession.endowment()) + me.lama * self.subsession.h() - self.subsession.tau()*(me.t + self.subsession.endowment())),
            my_assets=me.t + self.subsession.endowment(),
            my_trading=me.t,
            my_trading_word='Bought' if me.t > 0 else 'Sold' if me.t < 0 else 'No trade',
            trading_profit=(me.t) * self.group.price * -1,
        )

class Novoting(Page):
    def is_displayed(self):
        if self.subsession.config is not None:
            if self.subsession.voting_stage() == True:
                return self.player.t < 0
            else:
                return self.subsession.voting_stage() == True
        else:
            return self.subsession.config is not None

    def vars_for_template(self):
        me = self.player
        return dict(
            endowment= self.subsession.endowment(),
            tau= int(self.subsession.tau()),
            my_lama = me.lama,
            private_benefit= int(me.lama*self.subsession.h()),
            value_asset= int(self.subsession.v()*(me.t + self.subsession.endowment())),
            net_private_benefit= int(self.subsession.v()*(me.t + self.subsession.endowment()) + me.lama * self.subsession.h() - self.subsession.tau()*(me.t + self.subsession.endowment())),
            my_assets=me.t + self.subsession.endowment(),
            my_trading=me.t,
            my_trading_word='Bought' if me.t > 0 else 'Sold' if me.t < 0 else 'No trade',
            trading_profit=(me.t) * self.group.price * -1,
        )




class ResultsWaitPage2(WaitPage):

    def is_displayed(self):
        return self.subsession.config is not None

    after_all_players_arrive = 'set_payoffs'

    body_text = "Waiting for other participants to submit their choices."


class Results(Page):

    def is_displayed(self):
        return self.subsession.config is not None
    """Players payoff: How much each has earned"""

    def vars_for_template(self):
        me = self.player
        return dict(
            my_assets= me.t+self.subsession.endowment(),
            my_trading= me.t,
            my_trading_word= 'Bought' if me.t > 0 else 'Sold' if me.t < 0 else 'No trade',
            proposal_accept= 'Accepted' if self.group.policy>0 else 'Rejected',
            private_benefit= int(self.group.policy * (me.lama * self.subsession.h())),
            votes_accept= sum([p.vote*(self.subsession.endowment()+p.t) for p in self.group.get_players()]),
            votes_reject= self.subsession.players_per_group()- sum([p.vote * (self.subsession.endowment() + p.t) for p in self.group.get_players()]),
            asset_value= float(self.subsession.v()- self.group.policy*self.subsession.tau()),
            asset_profit= (self.subsession.v() - self.group.policy*self.subsession.tau())*(me.t+self.subsession.endowment()),
            trading_profit= (me.t)*self.group.price*-1,

        )



class Survey(Page):

    def is_displayed(self):
        return self.round_number == self.subsession.num_rounds()

    form_model = 'player'
    form_fields = ['why_accept','other_accept','why_reject','other_reject','age', 'gender','major','gpa','political']

class Payment(Page):

    def is_displayed(self):
        return self.round_number == self.subsession.num_rounds()

    def vars_for_template(self):
        return {
            'payoff': self.participant.payoff.to_real_world_currency(self.session),
        }


page_sequence = [Introduction, News, Market, ResultsWaitPage1, Voting, Novoting,
                 ResultsWaitPage2, Results, Survey, Payment]