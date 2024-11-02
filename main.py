# This is a sample Python script.
import random
from random import randint

BLOCK_LOOKAHEAD = 8

class EventLog:
    def __init__(self):
        self.event_log = []

    def add_event(self, event):
        self.event_log.append(event)

    def get_event_log(self):
        return self.event_log

class Run:
    def __init__(self, harberger_tax_rate):
        self.blockchain = BlockChain(harberger_tax_rate)
        self.round_counter = 0
        self.event_log = EventLog()
        self.harberger_tax_rate = harberger_tax_rate

    def increment_round_counter(self):
        self.round_counter += 1
        self.blockchain.increment_block_counter()

    def get_round_counter(self):
        return self.round_counter

    def log_event(self, event):
        self.event_log.add_event(event)

    def get_event_log(self):
        return self.event_log.get_event_log()

    def get_blockchain(self):
        return self.blockchain

# TODO: improve it later to account for market share
class HarbergerTaxFunction:
    def __init__(self, base_tax_rate: float):
        self.base_tax_rate = base_tax_rate

    def calculate_per_block_tax(self, valuation: int, market_share: float, blocks_proposed: int):
        # let the market settle in the first 10000 blocks
        # if blocks_proposed < 10000:
        #     return valuation * self.base_tax_rate
        #
        # if market_share > 0.40:
        #     return market_share * valuation

        return valuation * self.base_tax_rate

class BlockChain:
    def __init__(self, harberger_tax_rate):
        self.block_to_proposer_map = {}
        self.block_lease_holders_map = {}
        self.total_revenue = 0
        self.block_counter = 0
        self.builder_map = BuilderMap()
        self.orderflow_provider_map = OrderFlowProviderMap()
        self.harberger_tax_function = harberger_tax_rate

    def increment_block_counter(self):
        self.block_counter += 1

    def get_block_counter(self):
        return self.block_counter

    def add_block_to_proposer_map(self, block_number, proposer_name, valuation):
        self.block_to_proposer_map[block_number] = (proposer_name, valuation)

    def get_builder_market_share(self, name):
        total_blocks = len(self.block_to_proposer_map.items())
        total_blocks_proposed = 0
        for block_number, proposer in self.block_to_proposer_map.items():
            if proposer[0] == name:
                total_blocks_proposed += 1

        return total_blocks_proposed / total_blocks

    def get_builder_market_share_map(self):
        market_share_map = {}
        total_blocks = len(self.block_to_proposer_map.items())
        if total_blocks == 0:
            return market_share_map

        for name, builder in self.builder_map.builder_map.items():
            total_blocks_proposed = 0
            for block_number, proposer in self.block_to_proposer_map.items():
                if proposer[0] == name:
                    total_blocks_proposed += 1

            market_share_map[name] = total_blocks_proposed / total_blocks

        return market_share_map

    def get_proposer_name(self, block_number):
        return self.block_to_proposer_map[block_number]

    def add_block_lease_holders_map(self, block_number, lease_holder_name, valuation):
        self.block_lease_holders_map[block_number] = (lease_holder_name, valuation)

    def get_lease_holder_name(self, block_number):
        return self.block_lease_holders_map[block_number]

    def remove_block_lease(self, block_number):
        del self.block_lease_holders_map[block_number]

    def get_lease_holder_map(self):
        return self.block_lease_holders_map

    def add_builder(self, builder):
        self.builder_map.add_builder(builder)

    def add_order_flow_provider(self, order_flow_provider):
        self.orderflow_provider_map.add_order_flow_provider(order_flow_provider)

    # TODO - this will take in certain parameters as we add more information to the
    # auction like the block valuation etc
    def run_builder_auction(self, lookahead=BLOCK_LOOKAHEAD):
        builder_market_share_map = self.get_builder_market_share_map()

        return self.builder_map.run_builder_auction(builder_market_share_map, self.get_block_counter(), self.harberger_tax_function, lookahead)

    def add_revenue(self, revenue):
        self.total_revenue += revenue

    def get_total_revenue(self):
        return self.total_revenue


class Builder:
    def __init__(self, name: str, min_bid: int, valuation_range: list):
        self.name = name
        self.valuation_range = valuation_range
        self.blocks_proposed = 0
        self.min_bid = min_bid

    def get_valuation_range(self):
        return self.valuation_range

    def increment_valuation_range(self, increment):
        self.valuation_range[0] += increment
        self.valuation_range[1] += increment

    def get_blocks_proposed(self):
        return self.blocks_proposed

    def get_valuation(self, harberger_tax_rate: HarbergerTaxFunction, builder_market_share, total_blocks, lookahead):
        # return a random number in the valuation list
        start, end = self.valuation_range
        valuation = random.randint(start, end)
        per_block_tax = harberger_tax_rate.calculate_per_block_tax(valuation, builder_market_share, total_blocks)
        print("looking ahead", lookahead, "blocks")
        post_tax_valuation = valuation - per_block_tax * lookahead
        if post_tax_valuation < 0:
            return self.min_bid

        # we assume builders just want to stick to their true valuation - taxes
        # as we vary the tax rate based on market share, we will observe that bigger builder
        # valuations will be dragged down by the tax rate and smaller builders will get a chance
        # to win the block auction.
        return post_tax_valuation

class BuilderMap:
    def __init__(self):
        self.builder_map = {}

    def add_builder(self, builder: Builder):
        self.builder_map[builder.name] = builder

    def get_builder(self, name):
        return self.builder_map[name]

    def run_builder_auction(self, builder_market_share_map, total_blocks_proposed, harberger_tax_rate, lookahead):
        print("**** START AUCTION ****")
        # run the builder auction and return the name of the winning builder
        highest_valuation, winner_name = 0, ""
        for name, builder in self.builder_map.items():
            builder_market_share = 0.0
            if name in builder_market_share_map.keys():
                builder_market_share = builder_market_share_map[name]

            valuation = builder.get_valuation(harberger_tax_rate, builder_market_share, total_blocks_proposed, lookahead)
            print("Valuation for", name, "is", valuation)
            if valuation > highest_valuation:
                highest_valuation = valuation
                winner_name = name

        print("**** END AUCTION ****")
        return highest_valuation, winner_name

class OrderFlowProvider:
    def __init__(self, name: str, value_add: int, market_share_tolerance: int):
        self.name = name
        # the amount of value, the orderflow provider increases the builder's valuation by
        self.value_add = value_add
        # the market share post which the order flow which consider a builder
        self.market_share_tolerance = market_share_tolerance
        self.builders_sending_to = []

    def get_name(self):
        return self.name

    def get_value_add(self):
        return self.value_add

    def get_market_share_tolerance(self):
        return self.market_share_tolerance

    def send_to_builder(self, builder_name):
        self.builders_sending_to.append(builder_name)

class OrderFlowProviderMap:
    def __init__(self):
        self.order_flow_provider_map = {}

    def add_order_flow_provider(self, order_flow_provider: OrderFlowProvider):
        self.order_flow_provider_map[order_flow_provider.name] = order_flow_provider

    def get_order_flow_provider(self, name):
        return self.order_flow_provider_map[name]



class BeginRoundEvent:
    def __init__(self, round_number: int):
        self.round_number = round_number

    def get_round_number(self):
        return self.round_number

    def __repr__(self):
        return f"BeginRoundEvent: {self.round_number}"

    # TODO: Add a handle function later

class EndRoundEvent:
    def __init__(self, round_number: int):
        self.round_number = round_number

    def get_round_number(self):
        return self.round_number

    def __repr__(self):
        return f"EndRoundEvent: {self.round_number}"

    # TODO: Add a handle function later


class AddBuilderEvent:
    def __init__(self, builder: Builder):
        self.builder = builder

    def __repr__(self):
        return f"AddBuilderEvent: {self.builder.name}"

    # TODO: Add a handle function later


class AddOrderFlowProviderEvent:
    def __init__(self, order_flow_provider: OrderFlowProvider):
        self.order_flow_provider = order_flow_provider

    def __repr__(self):
        return f"AddOrderFlowProviderEvent: {self.order_flow_provider.name}"

    # TODO: Add a handle function later


class BlockProposalEvent:
    def __init__(self, block_number, block_proposer):
        self.block_number = block_number
        self.block_proposer = block_proposer

    def __repr__(self):
        return f"BlockProposalEvent: {self.block_number} by {self.block_proposer}"

class BlockLeaseAuctionEvent:
    def __init__(self, block_number: int):
        self.block_number = block_number

    def __repr__(self):
        return f"BlockLeaseAuctionEvent: {self.block_number}"

    # TODO: Add a handle function later


class ReviewBlockLeasesEvent:
    def __init__(self, block_number: int):
        self.block_number = block_number

    def __repr__(self):
        return f"ReviewBlockLeasesEvent: {self.block_number}"

    # TODO: Add a handle function later

def main():
    fixed_harberger_tax_rate = HarbergerTaxFunction(0.1)

    run = Run(fixed_harberger_tax_rate)
    blockchain = run.get_blockchain()
    # block number to special event
    special_event_map = {}

    # builder1 = Builder("Builder1", 50, [100, 200])
    # builder2 = Builder("Builder2", 40, [100, 150])
    # builder3 = Builder("Builder3", 70, [50, 125])
    # builder4 = Builder("Builder4", 30, [50, 75])
    # builder5 = Builder("Builder5", 50, [50, 100])

    builder1 = Builder("Builder1", 50, [200, 230])
    builder2 = Builder("Builder2", 50, [100, 210])
    builder3 = Builder("Builder3", 50, [150, 220])
    builder4 = Builder("Builder4", 50, [50, 100])
    builder5 = Builder("Builder5", 50, [50, 100])


    blockchain.add_builder(builder1)
    blockchain.add_builder(builder2)
    blockchain.add_builder(builder3)
    blockchain.add_builder(builder4)
    blockchain.add_builder(builder5)

    order_flow_provider1 = OrderFlowProvider("OrderFlowProvider1", 10, 5)
    order_flow_provider2 = OrderFlowProvider("OrderFlowProvider2", 50, 10)

    blockchain.add_order_flow_provider(order_flow_provider1)
    blockchain.add_order_flow_provider(order_flow_provider2)

    while run.get_round_counter() < 30000:
        # each loop is a round
        current_round = run.get_round_counter()
        print("Current Round:", current_round)

        # each round starts with a BeginRoundEvent
        begin_round_event = BeginRoundEvent(run.get_round_counter())
        run.log_event(begin_round_event)

        #Run the block lease review
        # Go through each lease and check if other builders have a new valuation which outbids the lease
        # if so, then we change the lease holder
        review_block_lease_event = ReviewBlockLeasesEvent(current_round)
        # get all the builder valuations
        new_lease_map = {}
        for round, (lease_holder_name, valuation) in blockchain.block_lease_holders_map.items():
            # TODO - this code is dumb
            lookahead = round - current_round
            # lock the lease 2 blocks before the current block
            if lookahead > 2:
                print("Reviewing Block", round, "leased to", lease_holder_name, "with valuation", valuation)

                new_valuation, winner_name = blockchain.run_builder_auction(lookahead)
                if new_valuation > valuation:
                    print("Block", round, "is being outbid by", winner_name, "with valuation", new_valuation)
                    # new_valuation = new_valuation
                    new_lease_map[round] = (winner_name, new_valuation)

        # update the lease holder map
        for round, (lease_holder_name, valuation) in new_lease_map.items():
            blockchain.block_lease_holders_map[round] = (lease_holder_name, valuation)

        run.log_event(review_block_lease_event)

        # Run the block lease auction for current block + 8
        # all the builders reveal their valuations and we just pick the highest one
        block_lease_auction_event = BlockLeaseAuctionEvent(current_round + BLOCK_LOOKAHEAD)
        print("Starting Block Lease Auction for block", current_round + BLOCK_LOOKAHEAD)
        valuation, winner_name = blockchain.run_builder_auction()
        print("Block Lease Auction for block", current_round + BLOCK_LOOKAHEAD, "won by", winner_name, "with valuation", valuation)

        # add the winner to the builder to license map
        blockchain.add_block_lease_holders_map(current_round + BLOCK_LOOKAHEAD, winner_name, valuation)
        run.log_event(block_lease_auction_event)

        # look if there is a current block lease holder
        if not current_round < BLOCK_LOOKAHEAD:
            current_block_lease_holder, valuation = blockchain.get_lease_holder_name(current_round)
            block_proposal_event = BlockProposalEvent(current_round, current_block_lease_holder)
            blockchain.add_block_to_proposer_map(current_round, current_block_lease_holder, valuation)
            blockchain.add_revenue(valuation)
            blockchain.remove_block_lease(current_round)
            print("Block", current_round, "is proposed by", current_block_lease_holder, "with valuation", valuation)
            run.log_event(block_proposal_event)


        # orderflow providers will choose the builders to send to based on their market share

        # each round ends with an EndRoundEvent
        end_round_event = EndRoundEvent(run.get_round_counter())
        run.log_event(end_round_event)

        run.increment_round_counter()

    print("Block Proposers:")
    for block_number, proposer in blockchain.block_to_proposer_map.items():
        print("Block", block_number, "is proposed by", proposer)

    print("Total Blockchain Revenue:", blockchain.get_total_revenue())

    print("Builder Market shares:")
    for name, builder in blockchain.builder_map.builder_map.items():
        print("Market share for", name, "is", blockchain.get_builder_market_share(name))

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
