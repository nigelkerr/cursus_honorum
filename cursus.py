
import esper
import random
from dataclasses import dataclass as component
import dataclasses
from collections import defaultdict
from enum import Enum
import roman
import logging
import datetime

# HYPER-PARAMETERS
TICK = 0.01
TICK_INCR = 0.1
ELECTION_BUMP_TO_VIBES = 0.2
HOW_MANY_PER_GENERATION = 72
STARTING_SENATOR_AGE = 45
STARTING_SENATE_SIZE = 100
MORTALITY_CHANCE = [
    0.001,
    0.002,
    0.008,
    0.025,
    0.075,
    0.15,
    0.5
]
# /HYPER-PARAMETERS

logger = logging.getLogger(__name__)
logging.basicConfig(filename=f'cursus_log_{datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y%m%dt%H%M%S")}.log', encoding='utf-8', level=logging.DEBUG)

@component
class Year:
    auc: int

@component
class Named:
    name: str

@component
class Aged:
    years: int

class Class(Enum):
    Plebeian = 1
    Patrician = 2
    Both = 3

# start with assumption that they can repeat
# these should be hyper-parameters
class Magistracy(Enum):
    # some of these after cohort size appointed
    MilitaryTribune = (1, 36, 26, Class.Both, 1)
    Quaestor = (2, 8, 30, Class.Both, 1)
    TribuneOfThePlebs = (3, 4, 30, Class.Plebeian, 1)
    Aedile = (4, 2, 36, Class.Plebeian, 1)
    CuruleAedile = (4, 2, 36, Class.Patrician, 1)
    Praetor = (5, 4, 39, Class.Both, 1)
    # these on special events, appointed
    ProPraetor = (5, 0, 40, Class.Both, 1)
    Consul = (6, 2, 42, Class.Both, 1)
    # these on special events, appointed
    ProConsul = (6, 0, 43, Class.Both, 1)
    # want these every fith year
    Censor = (7, 2, 43, Class.Patrician, 5)

    def __init__(self, rank, cohort_size, usual_age, class_requirement, year_frequency):
        self.rank = rank
        self.cohort_size = cohort_size
        self.usual_age = usual_age
        self.class_requirement = class_requirement
        self.year_frequency = year_frequency

# driving from https://en.wikipedia.org/wiki/Cursus_honorum#/media/File:Cursus.png ftm
RESUME_REQS = {
    Magistracy.Quaestor: [Magistracy.MilitaryTribune],
    Magistracy.TribuneOfThePlebs: [Magistracy.MilitaryTribune, Magistracy.Quaestor],
    Magistracy.Aedile: [Magistracy.MilitaryTribune, Magistracy.Quaestor],
    Magistracy.CuruleAedile: [Magistracy.MilitaryTribune, Magistracy.Quaestor],
    Magistracy.Praetor: [Magistracy.MilitaryTribune, Magistracy.Quaestor],
    Magistracy.ProPraetor: [Magistracy.MilitaryTribune, Magistracy.Quaestor, Magistracy.Praetor],
    Magistracy.Consul: [Magistracy.MilitaryTribune, Magistracy.Quaestor, Magistracy.Praetor],
    Magistracy.ProConsul: [Magistracy.MilitaryTribune, Magistracy.Quaestor, Magistracy.Praetor, Magistracy.Consul],
    Magistracy.Censor: [Magistracy.MilitaryTribune, Magistracy.Quaestor, Magistracy.Praetor, Magistracy.Consul],
}

@component
class Order:
    order: Class

@component
class Office:
    office: Magistracy

@component
class Elect:
    office: Magistracy

@component
class Reputation:
    vibes: float
    held_offices: list[Magistracy] = dataclasses.field(default_factory=list)

@component
class Senator:
    inducted_age: int
    inducted_when: int

# consider some way for families to have vibes, and for oddity families
NOMEN = ['Julius', 'Fabius', 'Sempronius', 'Verginius', 'Valerius', 'Horatius', 
            'Junius', 'Excretius', 'Excrutius', 'Marius', 'Lichius', 'Flugblogius', 
            'Gracchus', 'Furius', 'Dickus']

PRONOMEN = [
    'Agrippa', 'Appius', 'Aulus', 'Bigus', 'Caeso', 'Decimus', 'Faustus',
    'Gaius', 'Gnaeus', 'Hostus', 'Lucius', 'Mamercus', 'Manius', 'Marcus',
    'Mettius', 'Nonus', 'Numerius', 'Octavius', 'Opiter', 'Paullus',
    'Postumus', 'Proculus', 'Publius', 'Quintus', 'Septimus', 'Sertor',
    'Servius', 'Sextus', 'Spurius', 'Statius', 'Tiberius', 'Titus',
    'Tullus', 'Vibius', 'Volesus', 'Vopiscus',
]

def choose_nomen():
    return random.choice(NOMEN)
def choose_pronomen():
    return random.choice(PRONOMEN)

def this_year():
    return esper.get_component(Year)[0][1].auc
def this_year_roman():
    return roman.toRoman(this_year())

def incr_year():
    esper.get_component(Year)[0][1].auc += 1

def display_consuls_elect():
    consuls = list(filter(lambda m: m[1][0].office == Magistracy.Consul, esper.get_components(Elect,Named)))
    names = list(map(lambda c: c[1][1].name, consuls))
    return " and ".join(names)

def display_military_tribunes():
    return "numerous"

def affect_reputation(magistracy, values):
    total = sum(values)
    magistrates = list(filter(lambda m: m[1][0].office == magistracy, esper.get_components(Office,Reputation)))
    for magistrate in magistrates:
        magistrate[1][1].vibes += total


class TheYearHappensProcessor(esper.Processor):

    def process(self):
        global TICK
        economics = random.random() - 0.5
        military = random.random() - 0.5
        social = random.random() - 0.5

        print(f"In this year, economics were {economics}, military was {military} and social was {social}.") ## get the Partial Historians criteria...

        affect_reputation(Magistracy.Consul, [economics, military*2.0, social])
        affect_reputation(Magistracy.MilitaryTribune, [military])

        logger.info(f"Year {this_year()} population size: {self.pop_size()} and distribution: {self.pop_dist()}")

        # handle dying in office by various means

    def pop_size(self):
        return len(esper.get_component(Aged))

    def pop_dist(self):
        ages = defaultdict(int)
        for person in esper.get_component(Aged):
            ages[person[1].years] += 1
        return ' '.join([f"{age}:{ages[age]}" for age in sorted(ages)])

class ElectionsProcessor(esper.Processor):

    def process(self):
        # find all the people about the right age and order, 
        # and resumue,
        # have them stand for election

        # lets allow repeat office holders for now,
        # although if you've made it to the senate, maybe you don't care so much?

        for magistracy in Magistracy:

            # handles the censor case
            if this_year() % magistracy.year_frequency != 0:
                continue

            # xyzzy add criteria about generally having held the right offices,
            # and not already standing for some other post thus far this year.

            eligible = self.appropriate_age_and_order(magistracy.usual_age, magistracy.class_requirement)
            eligible = self.appropriate_resume(eligible, magistracy)
            standing = eligible # for laughs now, trim this sometime to a more reasonable number

            how_many = magistracy.cohort_size
            vote_portions = [random.randrange(100) for _ in range(len(standing))]
            results = zip(standing, vote_portions)
            winners = sorted(results, key=lambda r: r[1],reverse=True)[:how_many]

            # xyzzy describe the voting somehow...
            for p in winners:
                esper.add_component(p[0], Elect(magistracy))
                esper.component_for_entity(p[0], Reputation).vibes += ELECTION_BUMP_TO_VIBES

    # return entity ids
    def appropriate_resume(self, candidates, magistracy):
        eligible = []
        for c in candidates:
            if (magistracy in RESUME_REQS and self.sufficient_resume(magistracy, c)) or magistracy == Magistracy.MilitaryTribune:
                eligible.append(c)
        return eligible

    def sufficient_resume(self, magistracy, c):
        return all(z in esper.component_for_entity(c, Reputation).held_offices for z in RESUME_REQS[magistracy])

    # return entity ids
    def appropriate_age_and_order(self, age, class_req):
        retval = []
        for person in esper.get_components(Aged, Order):
            if person[1][0].years in range( age - 3, age + 3 ):
                if class_req == Class.Both or person[1][1].order == class_req:
                    retval.append(person[0])
        return retval

class AgingProcessor(esper.Processor):

    def they_happen_to_die(self, age):
        # we want younger people to generally
        # survive more than older people.
        # find a table more anchored in the ancient mediterranean.
        chance = random.random()
        if age <= 20:
            return chance < MORTALITY_CHANCE[0]
        if age <= 30:
            return chance < MORTALITY_CHANCE[1]
        if age <= 40:
            return chance < MORTALITY_CHANCE[2]
        if age <= 50:
            return chance < MORTALITY_CHANCE[3]
        if age <= 60:
            return chance < MORTALITY_CHANCE[4]
        if age <= 70:
            return chance < MORTALITY_CHANCE[5]
        return chance < MORTALITY_CHANCE[6]

    def handle_death(self, ent):
        # the consequences of a given death need to be handled: suffect appointments, for example
        logger.info(f"Year {this_year()} {esper.component_for_entity(ent, Named).name} died, at age {esper.component_for_entity(ent, Aged).years}.")
        esper.delete_entity(ent)

    def process(self):
        died = 0
        for person in esper.get_component(Aged):
            person[1].years += 1
            if self.they_happen_to_die(person[1].years):
                died += 1
                self.handle_death(person[0])
        print(f"This year, {died} elites died.")
        # create some new people
        for person in range(int(HOW_MANY_PER_GENERATION * 1.5)):
            make_a_person(16)

class ChangeYearsProcessor(esper.Processor):

    def process(self):

        end_of_year()
        # magistrates who served removed from posts, added to held_offices
        for magistracy in Magistracy:
            for p in list(filter(lambda m: m[1].office == magistracy, esper.get_component(Office))):
                esper.remove_component(p[0], Office)
                esper.component_for_entity(p[0], Reputation).held_offices.append(magistracy)

        # elect magistrates put in new offices
        for magistracy in Magistracy:
            for p in list(filter(lambda m: m[1].office == magistracy, esper.get_component(Elect))):
                esper.remove_component(p[0], Elect)
                esper.add_component(p[0], Office(magistracy))

        # is there a censor?  who should be put in the senate?
        induction_year = this_year() + 1 # uh
        if len(list(filter(lambda o: o[1].office == Magistracy.Censor, esper.get_component(Office)))):
            print(f"It is year {this_year_roman()}, and there is a census:")
            print(f"    There are {len(esper.get_component(Aged))} elites.")
            print(f"    The Senate has {len(esper.get_component(Senator))} members.")
            added = []
            for enough in esper.get_component(Reputation):
                if self.is_already_a_senator(enough[0]):
                    continue
                if Magistracy.Quaestor in enough[1].held_offices:
                    added.append(enough[0])
                    esper.add_component(enough[0], Senator(esper.component_for_entity(enough[0], Aged).years, induction_year))
                    logger.info(f"Year {this_year()} added to the senate this year of {induction_year}: {esper.get_components(enough[0])}")
            print(f"    The censors inducted elites of sufficient status numbering {len(added)} to the Senate.")

        print(f"The senate stands ready, at {len(esper.get_component(Senator))} members.")

    def is_already_a_senator(self, pent):
        try:
            esper.component_for_entity(pent, Senator)
            return True
        except KeyError:
            return False

def display_magistrates(magistracy):
    m = get_magistrates(magistracy)
    names = list(map(lambda c: esper.component_for_entity(c, Named).name, m))
    return " and ".join(names)

def get_magistrates(m):
    return list(map(lambda c: c[0], filter(lambda c: c[1].office == m, esper.get_component(Office))))

def there_are_censors():
    if len(get_magistrates(Magistracy.Censor)):
        return True
    if this_year() % 5 == 0:
        logger.error(f"In {this_year()} we have no censors but div by 5")
    return False

def beginning_of_year():
    print(f"Now begins the year {this_year_roman()} since the founding of Brome.")
    if there_are_censors():
        print(f"The censors for the year are {display_magistrates(Magistracy.Censor)}.")
    print(f"The consuls for the year are {display_magistrates(Magistracy.Consul)}.")
    print(f"The praetors for the year are {display_magistrates(Magistracy.Praetor)}.")
    print(f"The quaestors for the year are {display_magistrates(Magistracy.Quaestor)}.")
    print(f"The curule aediles for the year are {display_magistrates(Magistracy.CuruleAedile)}.")
    print(f"The aediles for the year are {display_magistrates(Magistracy.Aedile)}.")
    print(f"The tribunes of the plebs for the year are {display_magistrates(Magistracy.TribuneOfThePlebs)}.")
    print(f"The military tribunes for the year are {display_military_tribunes()}.")
    print()

def end_of_year():
    print(f"Now ends the year {this_year_roman()} since the founding of Brome.")
    if there_are_censors():
        print(f"The censors for the year were {display_magistrates(Magistracy.Censor)}.")
    print(f"The consuls for the year were {display_magistrates(Magistracy.Consul)}.")
    print(f"The praetors for the year were {display_magistrates(Magistracy.Praetor)}.")
    print(f"The quaestors for the year were {display_magistrates(Magistracy.Quaestor)}.")
    print(f"The curule aediles for the year were {display_magistrates(Magistracy.CuruleAedile)}.")
    print(f"The aediles for the year were {display_magistrates(Magistracy.Aedile)}.")
    print(f"The tribunes of the plebs for the year were {display_magistrates(Magistracy.TribuneOfThePlebs)}.")
    print(f"The military tribunes for the year were {display_military_tribunes()}.")
    print()

def setup():
    no_magistracy = list()
    magistrates = list()

    esper.create_entity(Year(1))

    possible_senators = []

    for age in range(17,75):
        # get a real population distribution
        for starting in range(HOW_MANY_PER_GENERATION):
            person = make_a_person(age)
            if age >= STARTING_SENATOR_AGE:
                possible_senators.append(person)
            no_magistracy.append(person)

    # corny assumption:
    # people at this level of wealth influence, roughly half-and-half patrician and plebeian
    patricians = list(filter(lambda ent: esper.component_for_entity(ent, Order).order == Class.Patrician, no_magistracy))
    plebeians = list(filter(lambda ent: esper.component_for_entity(ent, Order).order == Class.Plebeian, no_magistracy))

    # identify the current office-holders for first year
    for m in Magistracy:
        for c in range(m.cohort_size):
            winner = None
            if m.class_requirement == Class.Patrician:
                winner = random.choice(patricians)
            elif m.class_requirement == Class.Plebeian:
                winner = random.choice(plebeians)
            else:
                winner = random.choice(no_magistracy)

            if winner in patricians:
                patricians.remove(winner)
            if winner in plebeians:
                plebeians.remove(winner)
            if winner in no_magistracy:
                no_magistracy.remove(winner)

            esper.add_component(winner, Office(m))
            esper.component_for_entity(winner, Aged).years = m.usual_age # heh
            esper.component_for_entity(winner, Reputation).vibes += ELECTION_BUMP_TO_VIBES
            esper.component_for_entity(winner, Reputation).held_offices.append(m)
            if m in RESUME_REQS:
                esper.component_for_entity(winner, Reputation).held_offices.extend(RESUME_REQS[m])
            magistrates.append(winner)
    
    # figure out who is in the senate originally
    # maybe this relates to families at some point, but start with a chance among ppl 45+
    induction_year = this_year()
    for senator in  random.choices(possible_senators, k=STARTING_SENATE_SIZE):
        logger.info(f"Year {this_year()} inducted to Senate: {esper.components_for_entity(senator)}")
        esper.add_component(senator, Senator(esper.component_for_entity(senator, Aged).years, induction_year))
    print(f"The senate stands ready.")

def make_a_person(aged):
    ent = esper.create_entity(Named(choose_pronomen() + " " + choose_nomen()), Reputation(0.1,[]), Aged(aged), Order(random.choice([Class.Patrician, Class.Plebeian])))
    logger.info(f"Year {this_year()} made a person {esper.components_for_entity(ent)}")
    return ent

def main():
    setup()
    
    esper.add_processor(TheYearHappensProcessor(), priority=1000)
    esper.add_processor(ElectionsProcessor(), priority=500)
    esper.add_processor(ChangeYearsProcessor(), priority=90)
    esper.add_processor(AgingProcessor(), priority=10)

    for i in range(100):
        beginning_of_year()
        esper.process()
        incr_year()

if __name__ == "__main__":
    main()
