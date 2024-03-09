import random
startingCash = 1500
minCashLimit = 25
maxTurns = 1000
highRiskBudgetCalc = 0.99
lowRiskBudgetCalc = 0.5
debugMode = False
dealsMade = 0

# BACKLOG
# Add unmortgage properties function
# Incl. property as part of rent payment if needed
# Add player behaviour config - willingness to trade!
 
class Property:
    def __init__(self, name, type, boardPos, setID, price, mortgage, housePrice, rent0, rent1, rent2, rent3, rent4, rent5, setSize):
        self.name = name
        # propType (str) = street, station or utility
        self.type = type
        # boardPos = (int) position on board, zero based starting at Go.
        self.boardPos = boardPos
        # setID = (int) ID of the set the property belongs to. Start Old Kent Road is in set 0.  Stations and utilities also use setID.
        self.setID = setID
        # purchase price of property
        self.price = price
        self.mortgage = mortgage
        self.housePrice = housePrice
        # rent0 = rent due with no houses
        self.rent0 = rent0
        # rent1 = due with 1 house
        self.rent1 = rent1
        self.rent2 = rent2
        self.rent3 = rent3
        self.rent4 = rent4
        # rent5 = rent due with Hotel 
        self.rent5 = rent5
        # number of houses built
        self.setSize = setSize
        self.numHouses = 0
        # ownerID = (int) ID of the owner of the property.  Use zero for the bank.
        self.ownerID = 0
        self.mortgaged = False
    
    def __str__(self):
        return f"Property name = {self.name} \n Property type = {self.type} \n Property boardPos = {self.boardPos} \n Property setID = {self.setID} \n" + \
            f"Property price = {self.price} \n Property mortgage = {self.mortgage} \n Property housePrice = {self.housePrice} \n Property numHouses = {self.numHouses} \n" + \
            f"Property rent0 = {self.rent0} \n Property rent1 = {self.rent1} \n Property rent2 = {self.rent2} \n Property rent3 = {self.rent3} \n Property rent4 = {self.rent4} \n Property rent5 = {self.rent5} \n Property setSize = {self.setSize} \n Property numHouses = {self.numHouses} \n"

# define squares class: 
class Square:
    def __init__(self, pos, type, name):
        self.pos = pos
        self.type = type
        self.name = name

# define board class:
class Board:
    def __init__(self, propData, squares):
        self.squares = []
        self.properties = []
        for item in propData:
            self.properties.append(Property(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11], item[12], item[13]))
        for s in squares:
            self.squares.append(Square(s[0], s[1], s[2]))

# define player class:
class Player:
    def __init__(self, name, piece, invRisk):
        self.name = name
        self.piece = piece
        self.position = 0
        self.cash = startingCash
        # properties list format: one array item for each property owned:
        # [prop square ID, number of houses built (5 for hotel), ismortgaged]
        # e.g. []
        self.properties = []
        self.isBankrupt = False
        self.inJail = False
        self.jailTurns = 0
        self.hasJailCards = 0
        self.invRisk = invRisk #houseInvRisk can be high or low.  How much of cash with player invest in houses
        #self.houseInvRisk = "low"
        self.houseInvSpread = "pile" #houseInvSpread is spread or pile.  This decides whether to concentrate house building in a single set or spread across multiple sets
        #self.houseInvSpread = "pile"
        self.houseInvTier = "cheap" #houseInvTier is cheap or expensive.  This decides whether player prefers to first develop cheaper sets (e.g. Old Kent Road) or expensive sets (e.g. Mayfair)
        #self.houseInvTier = "expensive"

    def __str__(self):
        strSelf = ""
        strPropPortfolio = "PROPERTIES OWNED:\n"
        for p in self.properties:
            strPropPortfolio = strPropPortfolio + str(p) + "\n"
        return f"Player name = {self.name}\n Player piece = {self.piece}\n Player pos = {self.position}\n Player.cash =  {self.cash}\n Player.isBankrupt = {self.isBankrupt}\n" + strPropPortfolio + "\n"

# function to roll two 6 sided dice and return the result:
def roll_dice():
    global debugMode
    roll_double = False
    die1 = random.randint(1,6)
    die2 = random.randint(1,6)
    if die1 == die2:
        roll_double = True
    return [(die1+die2), roll_double]

# function to move player around the board:
def move_player(player, num_spaces):
    global debugMode
    player.position = (player.position + num_spaces) % 40

# function to buy a property (from the bank):
def buy_property(player, property):
    global debugMode
    if property in player.properties:
        if debugMode: print(f"Error: buy_property. player = {player.name}; property = {property.name}\n Player already owns this property!")
        return False
    if player.cash < property.price:
        if debugMode: print(f"Error: buy_property. player = {player.name}; property = {property.name}\n Player does not have enough cash to buy property")
        return False
    if player.isBankrupt == True:
        if debugMode: print(f"Error: buy_property. player = {player.name}; property = {property.name}\n Player is already bankrupt.")
        return False   
    else:
        player.properties.append(property)
        player.cash -= property.price
        return True

# given a property that a player owns, returns true if the player owns the whole set, false otherewise:
def owns_whole_set(player, property):
    global debugMode
    propsOwnedInSet = len([p for p in player.properties if p.setID == property.setID])
    return (propsOwnedInSet == property.setSize)

def find_property(boardPos, properties):
    global debugMode
    for p in properties:
        if p.boardPos == boardPos:
            return p
    return False

# function to raise cash - e.g. if rent bill received is greater than cash in hand
def raise_cash(board, player, amount):
    global debugMode
    if player.cash > amount:
        if debugMode: print(f"Error: raise_cash. player = {player.name}; player cash = {player.cash}; amount needed = {amount}\n Player already has enough cash!")
        return True
    else:
        # start by selling houses
        sell_houses(board,player,amount)
    if player.cash > amount:
        return True
    else:
        # now mortgage your properties
        for p in player.properties:
            if p.mortgaged == False:
                if debugMode: print(f"Info: raise_cash will call mortgage_property with player = {player.name}, prop = {p.name} ismortgaged == {p.mortgaged}.")
                mortgage_property(player,p)
            if player.cash > amount:
                return True
    # if we haven't raised up to the required amount, return False
    if player.cash < amount:
        return False
    else:
        return True

# function to pay rent:
# p1 is the rent payer, p2 is the rent recipient
def pay_rent(board, p1, p2, property, diceRoll):
    global debugMode
    rent = 0
    propsInSet = (sum(p.setID == property.setID for p in p2.properties))
    if debugMode: print("pay_rent called: " + str(p1.name) + ", " + str(p2.name) + ", " + str(property.name))
    # if rent is mortgaged, no rent is due:
    if property.mortgaged == True:
        if debugMode: print(f"Error: pay_rent. player = {p1.name}; property = {property.name}; owner = {p2.name} \n property is mortgaged so no rent is due")
        return False
    # build rent process for stations:
    if property.type == "station":
        if propsInSet == 1:
            rent = property.rent0
        elif propsInSet == 2:
            rent = property.rent1
        elif propsInSet == 3:
            rent = property.rent2
        elif propsInSet == 4:    
            rent = property.rent3        
    elif property.type == "utility":
        if propsInSet == 2:
            rent = int(diceRoll[0] * property.rent1)
        else:
            rent = int(diceRoll[0] * property.rent0)
    elif property.type == "street":
        # base case where no houses are built:
        if property.numHouses == 0:
            if owns_whole_set(p2, property) == True:
                rent = (property.rent0 * 2)
            else:
                rent = property.rent0
        elif property.numHouses == 1:
            rent = property.rent1
        elif property.numHouses == 2:
            rent = property.rent2
        elif property.numHouses == 3:
            rent = property.rent3
        elif property.numHouses == 4:
            rent = property.rent4
        else:
            rent = property.rent5

    amount = rent - p1.cash

    if rent > p1.cash:
        raise_cash(board, p1, amount)
    if p1.cash > rent:
        p1.cash -= rent
        p2.cash += rent
        if debugMode: print(f"INFO: pay_rent. {p1.name} paid {rent} to {p2.name} for rent")
        return True
    else:
        propsRent = []
        propsVal = 0
        for p in p1.properties:
            propsRent.append(p)
            if p.mortgaged == True:
                propsVal += p.mortgage
            else:
                propsVal += p.price
            if ((propsVal + p1.cash) >= rent):
                break
            cashPart = rent - propsVal
            p1.cash -= cashPart
            p2.cash += cashPart
            for p in propsRent:
                p1.properties.remove(p)
                p2.properties.append(p)
            if debugMode: print(f"INFO: pay_rent. {p1.name} paid cash {cashPart} to {p2.name} for rent AND transferred the following properties to them:")
            for p in propsRent:
                if debugMode: print(f"{p.name}; mortgaged = {p.mortgaged}")
            if ((propsVal + cashPart) >= rent):
                return True
            else:
                p1.isBankrupt = True
                return True

# function to handle a player going to jail:
def go_to_jail(player):
    global debugMode
    player.inJail = True
    player.jailTurns = 1

# function to handle a player getting out of jail:
def get_out_of_jail(player):
    global debugMode
    return True

# function to sell a single house from a single property
def sell_house(player, property):
    global debugMode
    if property.numHouses == 0:
        if debugMode: print(f"Error: sell_house. player = {player.name}; property = {property.name}; property has no houses so houses cannot be sold")
        return False
    property.numHouses -= 1
    player.cash += (property.housePrice / 2)
    return True

def get_set_by_ID(board, setID):
    global debugMode
    return [p for p in board.properties if p.setID == setID]

def sell_houses_in_set(board, player, amount, property):
    global debugMode
    s = get_set_by_ID(board,property.setID)
    housePrice = s[0].price
    totalHouses = sum(p.numHouses for p in s)

    # if Set has zero houses on it
    if totalHouses == 0:
        if debugMode: print(f"ERROR: sell_houses_in_set = {player.name}; property set = {p.name}; All properties have zero houses already.")
        return amount
    
    # The case where we need to sell all houses and still not raising enough:
    if (totalHouses * (housePrice/2)) < amount:
        for p in s:
            while p.numHouses > 0:
                sell_house(player,p)
                amount -= (p.housePrice / 2)
                if debugMode: print(f"p.numHouses = {p.numHouses}")
    else:  
        # remaining case - partial sell of housing stock
        while (amount >= 0) and (totalHouses > 0):
            # find property in set with most houses
            mostDevProp = s[0]
            for p in s:
                if p.numHouses > mostDevProp.numHouses:
                    mostDevProp = p
            if mostDevProp.numHouses > 0:
                sell_house(player,mostDevProp)
                amount -= (p.housePrice/2)
    return amount

# function to sell houses or hotels as needed:
def sell_houses(board,player,amount):
    global debugMode
    if player.cash > amount:
        if debugMode: print(f"Error: sell_houses. player = {player.name}; amount = {amount}. Player already has cash > amount, no need to sell houses.")
        return False
    totalHouses = 0
    totalHouses = sum(p.numHouses for p in player.properties)
    if totalHouses == 0:
        if debugMode: print(f"Error: sell_houses. player = {player.name}; amount = {amount}. Player does not have any properties with houses.")
        return False
    amountRaised = 0
    # Check if player can raise enough cash by selling houses:
    if sum((p.numHouses * p.housePrice/2) for p in player.properties) > amount:
        if debugMode: print(f"Info: sell_houses. player {player.name} can raise {amount} cash by selling houses.")
        # Player needs to sell some not all of their houses  
        while amountRaised < amount:
            for p in reversed(player.properties):
                if p.numHouses > 0:
                    sell_house(player, p)
                    amountRaised += (p.housePrice / 2)
                    if (amountRaised >= amount):
                        return True
    else:
        # If all players housing stock is less than amount needed, sell them all!  
        for p in player.properties:
            while p.numHouses > 0:
                sell_house(player,p)
                return True

# function to handle a player mortgaging a property:
def mortgage_property(player, property):
    global debugMode
    if property.mortgaged == True:
        if debugMode: print(f"Error: mortgage_property. player = {player.name}; property = {property.name}; property is already mortgaged so cannot be mortaged")
        return False
    else:
        if property.numHouses > 0:
            while property.numHouses > 0:
                sell_house(player,property)
            if property.numHouses > 0:
                if debugMode: print(f"Error: mortgage_property. player = {player.name}; property = {property.name}; property has houses on it so cannot be mortaged")
            return False
        else:
            property.mortgaged = True
            player.cash += property.mortgage
            return True

# function to handle a player unmortgaging their properties:
def unmortgage_properties(player, budget):
    global debugMode
    for p in player.properties:
        unmortgage = p.mortgage * 1.1
        if p.mortgaged == True:
            if ((unmortgage) < budget) and (unmortgage < player.cash):
                unmortgage_property(player,p)
                budget -= unmortgage
        if budget < 0:
            break
    return True

# function to handle a player unmortgaging a property:
def unmortgage_property(player, property):
    global debugMode
    if (property.mortgage * 1.1) > player.cash:
        if debugMode: print(f"Error: unmortgage_property. player = {player.name}; property = {property.name}; player does not have enough cash, so property cannot be unmortaged")
        return False
    if property.mortgaged == False:
        if debugMode: print(f"Error: unmortgage_property. player = {player.name}; property = {property.name}; property is not mortgaged so cannot be unmortaged")
        return False
    else:
        property.mortgaged = False
        player.cash -= (property.mortgage * 1.1)
        return True

# function to handle a player declaring bankruptcy:
def declare_bankruptcy(player):
    global debugMode
    player.isBankrupt = True
    player.properties.clear()

# function to move a player around the board:
def move_player(player, num_spaces):
    global debugMode
    oldPos = player.position
    player.position = (player.position + num_spaces) % 40
    if debugMode: print(f"DEBUG: move_player {player.name} moved from position {oldPos} ")
    if (player.position < oldPos) and (num_spaces > 0):
        pass_go(player)

# function to process chance or community chest card outcomes
def process_card(player, board, card):
    global debugMode
    c = card
    if c[0] == "advanceto":
        pos = player.position
        newPos = c[2]
        mv = 0
        # check if target position is after Go.
        if newPos < pos:
            mv = (newPos+40) - pos
        else:
            mv = newPos - pos
        move_player(player,mv)
    elif c[0] == "gotojail":
        go_to_jail(player)
    elif c[0] == "goback":
        if c[2] < 0:
            # card is go back 3 spaces:
            move_player(player,-3)
        else:
            #card says go back to a square
            pos = player.position
            newPos = c[2]
            mv = newPos - pos
            if mv < 1:
                move_player(player, mv)
            else:
                mv = (pos+40) - newPos
                move_player(player, mv)
    elif c[0] == "pay" or c[0] == "receive":
        player.cash += c[2]
    elif c[0] == "jailfreecard":
        player.hasJailCards += 1
    elif c[0] == "repairs":
        houses = 0
        hotels = 0
        bill = 0
        for p in player.properties:
            if p.numHouses == 5:
                hotels += 1
            else:  
                houses += p.numHouses
        bill += (houses * c[2])
        bill += (hotels * c[3])
        player.cash += bill
        if debugMode: print(f"player {player.name} received house repairs card.  bill = {bill}")
    return

# function to handle a player drawing a chance card:
def draw_chance_card(player, board):
    global debugMode
    card = random.choice(chance_cards)
    if debugMode: print(f"Chance! {player.name} has drawn {card[1]}")
    process_card(player, board, card)
    return
            
# function to handle a player drawing a community chest card:
def draw_community_chest_card(player, board):
    global debugMode
    card = random.choice(community_chest_cards)
    if debugMode: print(f"Community Chest! {player.name} has drawn {card[1]}")
    process_card(player, board, card)
    return

# function to find owner of a given property
def find_owner(property, players):
    global debugMode
    for p in players:
        for prop in p.properties:
            if property.boardPos == prop.boardPos:
                return p
    # if no player has bought property, return False
    return False

# function to check if a player owns a property
def owns_property(player, property):
    global debugMode
    return (property in player.properties)

# function to build houses on a property
def build_house(player, property):
    global debugMode
    if player.cash < property.housePrice:
        if debugMode: print(f"Error: build_house. player = {player.name}; property = {property.name}\n Player does not have enough cash to build house")
        return False
    if property.numHouses > 4:
        if debugMode: print(f"Error: build_house. player = {player.name}; property = {property.name}\n Property already has > 4 houses")
        return False
    if property.type != "street":
        if debugMode: print(f"Error: build_house. player = {player.name}; property = {property.name}\n Property type is not street.  Cannot build house.")
        return False
    if property.mortgaged == True:
        if debugMode: print(f"Error: build_house. player = {player.name}; property = {property.name}\n Property is mortgaged.  Cannot build house.")
        return False
    if owns_whole_set(player, property) == False:
        if debugMode: print(f"Error: build_house. player = {player.name}; property = {property.name}\n Player does not own whole set.  Cannot build house.")
        return False
    # If we have passed all the above checks, lets build one house
    player.cash -= property.housePrice
    property.numHouses += 1
    if debugMode: print(f"DEBUG: Info: build_house. player = {player.name}; property = {property.name}\n built 1 house")
    return True

def is_set_fully_built(player, property):
    global debugMode
    if property.type != "street":
        if debugMode: print(f"ERROR: is_set_fully_built. set {property.name} is not type street.")
        return True
    else:
        set = [p for p in player.properties if (p.setID == property.setID) and (p.numHouses < 5)]
        if len(set) == 0:
            return True
        else:
            return False
   
# function to invest in houses on a set, given a defined budget
def develop_set(board, player, budget, setID):
    global debugMode
    # find the set to be developed
    s = get_set_by_ID(board, setID)
    housePrice = s[0].housePrice
    totalHouses = sum(p.numHouses for p in s)
    maxHouses = len(s) * 5
    
    if debugMode: print(f"DEBUG: develop_set: property set = {s[0].name}; maxHouses = {maxHouses}; totalHouses = {totalHouses}; budget = {budget}")

    # if Set is already max developed (hotels on all)
    if totalHouses == maxHouses:
        if debugMode: print(f"ERROR: develop_set player = {player.name}; property set = {p.name}; All properties are developed to the max.")
        return False
    
    # first calc number of houses to buy:
    numBuyHouses = int(budget // housePrice)
    
    # start loop for i houses to buy:
    for i in range(0,numBuyHouses):
        # find property in set with fewest houses
        leastDevProp = s[0]
        for p in s:
            if p.numHouses < leastDevProp.numHouses:
                leastDevProp = p
        # now build 1 house on least developed property
        if leastDevProp.numHouses < 5:
            build_house(player,leastDevProp)
    return True



def develop_properties(board, player, budget):
    global debugMode
    if debugMode: print(f"DEBUG - starting develop_properties with player = {player.name}; budget = {budget}")
    
    # List properties that could be developed:
    propsToDev = []
    for p in player.properties:
        if p.type == "street" and p.numHouses < 5 and owns_whole_set(player, p):
            propsToDev.append(p)

    # check to see if properties are fully developed:
    if len(propsToDev) == 0:
        if debugMode: print(f"ERROR: develop_properties.  All properties are fully developed already. player = {player.name}; budget = {budget}")
        return False
    else:
        # list the sets that the player owns:
        sets = []
        for p in propsToDev:
            if p.setID not in sets:
                sets.append(p.setID)
        if debugMode:
            print(f"DEBUG - running develop_properties with player = {player.name}; budget = {budget}")
            print(f"DEBUG - develop_properties: sets = {sets}")

        # select a set for development (most expensive?  least expensive?)

        if player.houseInvSpread == "pile":
                cheapestProp = min(propsToDev,key=lambda x:x.rent5)
                mostExpensiveProp = max(propsToDev,key=lambda x:x.rent5)
                if player.houseInvTier == "cheap":
                    develop_set(board,player,budget,cheapestProp.setID)
                else:
                    develop_set(board,player,budget,mostExpensiveProp.setID)
        else:
            # Check if player likes to invest in many sets (spread)
            budgetShare = budget / len(sets)
            for setID in sets:
                if budgetShare >= p.housePrice:
                    develop_set(board,player,budgetShare, p.setID)
    return True

# calculate a players budget based on their risk profile
def calc_budget(player):
    global debugMode
    budget = player.cash - minCashLimit
    if player.invRisk == "high":
        budget = player.cash * highRiskBudgetCalc
    else:
        budget = player.cash * lowRiskBudgetCalc
    return budget

# function to handle a player's turn:
def take_turn(player, players, board):
    global debugMode
    
    # start of turn - print player status
    if debugMode: print(f"take_turn: Start of turn {player.name}:")

    # if player is bankrupt - they don't play a turn
    if player.isBankrupt == True:
        if debugMode: print(f"take_turn: {player.name} is bankrupt - exit function")
        return
    
    if debugMode: print(player.name + " is on position " + str(player.position))

    # roll dice:
    diceRoll = roll_dice()
    if debugMode: print(player.name + " rolled a " + str(diceRoll[0]))

    # move player around the board:
    move_player(player, diceRoll[0])
    newPos = player.position
    if debugMode: print(player.name + " has moved to position " + str(newPos))

    # retrieve the square the player has landed on:
    sq = board.squares[newPos]
    if debugMode: print("square name = ", sq.name)

    # Check if Player has landed on property
    if sq.type == "property":
        # find the property object for this square
        if debugMode: print(f"DEBUG - take_turn calling find_property ({str(sq.pos)} {str(board.properties)})")
        p = find_property(sq.pos, board.properties)
        if debugMode: print("find_property returned ", p.name)

        # check to see if this player owns the property:
        p2 = find_owner(p,players)
        if p2 == player:
            # the player owns this property - no action
            pass
        elif p2 == False:
            # No one owns the property, maybe buy it?
            # TO DO - Add some player buying decision logic here?
            if calc_budget(player) > p.price:
                buy_property(player,p)
        else:
            if p.mortgaged == False:
                # pay rent
                pay_rent(board,player,p2,p,diceRoll)

    elif sq.type == "go":
        pass
    elif sq.type == "freepark":
        pass
    elif sq.type == "chance":
        draw_chance_card(player, board)
    elif sq.type == "commchest":
        # TO DO - Need to action community chest card
        draw_community_chest_card(player, board)
    elif sq.type == "jail":
        pass
    elif sq.type == "gotojail":
        go_to_jail(player)  
    elif sq.type == "tax":
        if sq.name == "Income Tax":
            player.cash -= 200
        else:
            player.cash -= 100
    else:
        pass

    # check for bankrupcy
    if player.cash < 0:
        raise_cash(board,player,(0-player.cash))
    if player.cash < 0:
        if debugMode: print(player.name + " is bankrupt!")
        player.isBankrupt = True
        return

    # Check to see if we can unmortgage properties:
    budget = calc_budget(player)
    unmortgage_properties(player,budget)

    # if player can invest in development, do that here:
    budget = calc_budget(player)
    if len([p for p in player.properties]) > 0: 
        # List properties that could be developed:
        propsToDev = False
        for p in player.properties:
            if p.type == "street" and p.numHouses < 5 and owns_whole_set(player, p):
                propsToDev = True
        # check to see if properties are fully developed:
        if propsToDev == True:
            develop_properties(board, player, budget)

    # Now look for trades
    budget = calc_budget(player)
    if budget > 300 and (len([p for p in player.properties]) > 0):
        do_trading(board,players,player)

    # end of turn - print player status
    if debugMode:
        print("End of turn:")
        print(player)
        print("===================")

# function to handle passing go:
def pass_go(player):
    global debugMode
    player.cash += 200

# Function for a player to scan their properties and identify potential trade:
def scan_for_trades(board, players, player):
    global debugMode
    if debugMode: print(f"scan_for_trades started ({board}, {players}, {player.name})")
    #first make a list of the sets represented in the portfolio
    sets = []
    for p in player.properties:
        if debugMode: print(f"{p.name}, setID = {p.setID} setSize = {p.setSize} ")
        if p.setID not in sets: 
            sets.append(p.setID)

    # Now use the set list to build a list of properties by set:
    # schema will be setID, numberHeld, setSize 
    propsBySet = []
    tempList = []
    for s in sets:
        propsBySet.append([
            s,
            sum(p.setID == s for p in player.properties),
            sum(p.setID == s for p in board.properties)
            ])
    if debugMode: print("propsBySet = ", propsBySet)
    foundOfferProp = False
    foundMissingProp = False
    for x in propsBySet:
        if x[2] - x[1] < 3:
            if debugMode: print("only 1-2 property missing in set = ", x[0])
            # Identify missing property
            targetSet = []
            for p in board.properties:
                if p.setID == x[0]:
                    targetSet.append(p)
            for q in targetSet:
                if q not in player.properties:
                    missingProp = q
                    if debugMode: print("missingProp =", missingProp)
                    if find_owner(q, players) == False:
                        break
                    else:
                        p2 = find_owner(q, players)
                        foundMissingProp = True
                        if debugMode: print("scan_for_targets calling find_owner with (owner of target prop) p2 = ", p2)
                        foundMissingProp = True
        if x[2] - x[1] == 2:
            for p in player.properties:
                if p.setID == x[0]:
                    offeredProp = p
                    foundOfferProp = True

        if foundOfferProp and foundMissingProp:
            if debugMode: 
                print(f"scan_for_trades found missingProp = {missingProp.name}; offeredProp = {offeredProp.name}")
                print("now calling offer_trade")            
            offer_trade(board,player,p2,missingProp,offeredProp)
            return True
        else:
            return False

# Function to order players properties into sets (list with sublist for each set / incomplete set owned), with setID as first item in each sublist:
def get_player_sets(board, players, player):
    global debugMode
    if len([p for p in player.properties]) == 0:
        if debugMode: print(f"ERROR - get_player_sets.  Player {player.name} does not own any properties")
        return False
    
    if debugMode: print(f"get_player_sets started ({board}, {players}, {player.name})")
    #first make a list of the sets represented in the portfolio
    sets = []
    for p in player.properties:
        if debugMode: print(f"{p.name}, setID = {p.setID} setSize = {p.setSize} ")
        if p.setID not in sets:
            sets.append(p.setID)
    # Now use the set list to build a list of properties by set:
    propsBySet = []
    for s in sets:
        tempList = []
        for p in player.properties:
            if p.setID == s:
                tempList.append(p)
        propsBySet.append(tempList)
                
    if debugMode:
        for s in propsBySet:
            print(f"DEBUG do_trading list sets functionality.")
            print(f"setID =  {s[0].setID}")
            for i in range (0, len(s)):
                print("set item = ", s[i].name)

    return propsBySet

# NEW Function to handle trading 
def do_trading(board, players, player):
    global debugMode
    sets = get_player_sets(board, players, player)
    if sets == False:
        if debugMode: print(f"ERROR - do_trading. sets input is boolean False. sets = {sets}")
    for s in sets:
        # First look for sets where we have 2/3 properties:
        if (len(s) == 2) and s[0].setSize == 3:
            if debugMode: print(f"DEBUG - do_trading. found a candidate set = {s[0].name}")
            # Find the property missing from this set:
            wholeSet = get_set_by_ID(board, (s[0].setID))
            for p in wholeSet:
                if p not in s:
                    targetProp = p

        #if (s[0].setSize) - (len(s)) == 1:
            #print(f"DEBUG - do_trading. found a candidate set = {s[0].name}")
            # Find the property missing from this set:
            #wholeSet = get_set_by_ID(board, (s[0].setID))
            #targetProp = list(set(wholeSet).difference(s))
            #break
        
            p2 = find_owner(targetProp, players)
            if p2 == False:
                # This means missing property is owned by the bank!
                continue
            budget = calc_budget(player)
            cashOffer = ((targetProp.price * 1.2) + 50)
            if budget > cashOffer:
                complete_propCash_trade(board,player,p2,targetProp,cashOffer)
                return True
            else:
                return False

# Function to offer a property trade (swap one property for another)
def offer_trade(board, offeringPlayer, targetPlayer, offeredProp, wantedProp):
    global debugMode
    if debugMode: 
        print(f"player {offeringPlayer.name} has offered a trade to {targetPlayer.name}:")
        print(f"offered Property = {offeredProp.name}")
        print(f"wanted Property = {wantedProp.name}")
    consider_trade_offer(board,offeringPlayer,targetPlayer,wantedProp,offeredProp)

def complete_propCash_trade(board, offeringPlayer, targetPlayer, wantedProp, cash):
    global debugMode
    global dealsMade
    if wantedProp not in targetPlayer.properties:
        if debugMode: print(f"ERROR complete_property_trade - wantedProp {wantedProp.name} not found in portfolio of player {targetPlayer.name}")
        return False
    else:
        offeringPlayer.properties.append(wantedProp)
        targetPlayer.properties.remove(wantedProp)
        offeringPlayer.cash -= cash
        targetPlayer.cash += cash
        dealsMade += 1
        return True
    
def complete_property_trade(board, offeringPlayer, targetPlayer, offeredProp, wantedProp, cash):
    global dealsMade
    global debugMode
    if wantedProp not in targetPlayer.properties:
        if debugMode: print(f"ERROR complete_property_trade - wantedProp {wantedProp.name} not found in portfolio of player {targetPlayer.name}")
        return False
    if offeredProp not in offeringPlayer.properties:
        if debugMode: print(f"ERROR complete_property_trade - offeredProp {offeredProp.name} not found in portfolio of player {offeringPlayer.name}")
        return False
    else:
        offeringPlayer.properties.remove(offeredProp)
        targetPlayer.properties.append(offeredProp)
        offeringPlayer.properties.append(wantedProp)
        targetPlayer.properties.remove(wantedProp)
        offeringPlayer.cash -= cash
        targetPlayer.cash += cash
        dealsMade += 1
        return True
   
def consider_trade_offer(board, offeringPlayer, targetPlayer, offeredProp, wantedProp):
    # review on behalf of target player
    # does the offered property complete a set?
    global debugMode
    setID = offeredProp.setID
    setSize = offeredProp.setSize
    propsInSet = sum(p.setID == setID for p in targetPlayer.properties)
    if (setSize - propsInSet == 1) or (propsInSet > 0):
        costDiff = wantedProp.price - offeredProp.price
        cash = costDiff
        if calc_budget(offeringPlayer) > cash:
            complete_property_trade(board, offeringPlayer, targetPlayer,offeredProp, wantedProp, cash)
            return True
    return False

def create_board(propData, sqs):
    global debugMode
    return Board(propData, sqs)

def create_players(playerData):
    global debugMode
    players = []
    for p in playerData:
        players.append(p)
    return players

# function to find the winner:
def find_winner(players, turns):
    global debugMode
    global dealsMade
    notBankrupt = 0
    for p in players:
        if not p.isBankrupt:
            notBankrupt += 1
    if notBankrupt == 1:
        # print a final report
        for p in players:
            if not p.isBankrupt:
                winner = p
            if debugMode:
                print("===============")
                print(f"player {p.name}")
                print (f"cash {p.cash}")
                print("Properties:")
                for props in p.properties:
                    print(f"{props.name}, houses = {props.numHouses}")
                print("===============")
        print(f"turns completed = {turns}")
        print(f"deals made = {dealsMade}")
        print(f"Winner cash = {winner.cash}")
        print(f"RESULT: {winner.name} is the winner!")

        return winner
    else:
        return None

# function to play the game:
def play_game(board, players):
    global debugMode
    global dealsMade
    turns = 0
    print("Welcome to Monopoly!")
    while find_winner(players, turns) == None:
        for p in players:
            if p.isBankrupt == False:
                take_turn(p, players, board)
                if debugMode: print("turn number " + str(turns) + " out of " + str(maxTurns) + " turns")
                turns += 1
                if turns > maxTurns:
                    print(f"NO RESULT: Game has taken {maxTurns} with no winner.")
                    print(f"deals made = {dealsMade}")
                    if debugMode:
                        for p in players:
                            print("===============")
                            print(f"player {p.name}")
                            print (f"cash {p.cash}")
                            print("Properties:")
                            for props in p.properties:
                                print(f"{props.name}")
                                print(f"Houses built = {props.numHouses}")
                            print("===============")
                    exit()

# Create some players        
x = [
    Player("Bob", "TopHat", "high"),
    #Player("Jules", "Car"),
    Player("Jane", "Boot", "high"),
    Player("Nas","Car", "high"),
    Player("2Pac", "T-Rex", "low")
]

# Create property data
propData = [
    ["Old Kent Road","street",1,0,60,30,50,2,10,30,90,160,250,2],
    ["Whitechapel Road","street",3,0,60,30,50,4,20,60,180,320,450,2],
    ["King Cross Station","station",5,1,200,100,0,25,50,100,200,0,0,4],
    ["The Angel Islington","street",6,2,100,50,50,6,30,90,270,400,550,3],
    ["Euston Road","street",8,2,100,50,50,6,30,90,270,400,550,3],
    ["Pentonville Road","street",9,2,120,60,50,8,40,100,300,450,600,3],
    ["Pall Mall","street",11,3,140,70,100,10,50,150,450,625,750,3],
    ["Electric Company","utility",12,4,150,75,0,4,8,0,0,0,0,2],
    ["Whitehall","street",13,3,140,70,100,10,50,150,450,625,750,3],
    ["Northumberland Avenue","street",14,3,160,80,100,12,60,180,500,700,900,3],
    ["Marylebone Station","station",15,1,200,100,0,25,50,100,200,0,0,4],
    ["Bow Street","street",16,5,180,90,100,14,70,200,550,750,950,3],
    ["Marlborough Street","street",18,5,180,90,100,14,70,200,550,750,950,3],
    ["Vine Street","street",19,5,200,100,100,16,80,220,600,800,1000,3],
    ["The Strand","street",21,6,220,110,150,18,90,250,700,875,1050,3],
    ["Fleet Street","street",23,6,220,110,150,18,90,250,700,875,1050,3],
    ["Trafalgar Square","street",24,6,240,120,150,20,100,300,750,925,1100,3],
    ["Fenchurch Street Station","station",25,1,200,100,0,25,50,100,200,0,0,4],
    ["Leicester Square","street",26,7,260,130,150,22,110,330,800,975,1150,3],
    ["Coventry Street","street",27,7,260,130,150,22,110,330,800,975,1150,3],
    ["Water Works","utility",28,4,150,75,0,4,8,0,0,0,0,2],
    ["Piccadilly","street",29,7,280,140,150,24,120,360,850,1025,1200,3],
    ["Regent Street","street",31,8,300,150,200,26,130,390,900,1100,1275,3],
    ["Oxford Street","street",32,8,300,150,200,26,130,390,900,1100,1275,3],
    ["Bond Street","street",34,8,320,160,200,28,150,450,1000,1200,1400,3],
    ["Liverpool Street Station","station",35,1,200,100,0,25,50,100,200,0,0,4],
    ["Park Lane","street",37,9,350,175,200,35,175,500,1100,1300,1500,2],
    ["Mayfair","street",39,9,400,200,200,50,200,600,1400,1700,2000,2]
]

# Create board squares data
squares = [
                [0,"go","Go"],
                [1,"property","Old Kent Road"],
                [2,"commchest","Community Chest"],
                [3,"property","Whitechapel Road"],
                [4,"tax","Income Tax"],
                [5,"property","Kings Cross Station"],
                [6,"property","The Angel Islington"],
                [7,"chance","Chance"],
                [8,"property","Euston Road"],
                [9,"property","Pentonville Road"],
                [10,"jail","Jail"],
                [11,"property","Pall Mall"],
                [12,"property","Electric Company"],
                [13,"property","Whitehall"],
                [14,"property","Northumberland Avenue"],
                [15,"property","Marylebone Station"],
                [16,"property","Bow Street"],
                [17,"commchest","Community Chest"],
                [18,"property","Marlborough Street"],
                [19,"property","Vine Street"],
                [20,"freepark","Free Parking"],
                [21,"property","Strand"],
                [22,"chance","Chance"],
                [23,"property","Fleet Street"],
                [24,"property","Trafalgar Square"],
                [25,"property","Fenchurch Street Station"],
                [26,"property","Leicester Square"],
                [27,"property","Coventry Street"],
                [28,"property","Water Works"],
                [29,"property","Piccadilly"],
                [30,"gotojail","Go to Jail"],
                [31,"property","Regent Street"],
                [32,"property","Oxford Street"],
                [33,"commchest","Community Chest"],
                [34,"property","Bond Street"],
                [35,"property","Liverpool Street Station"],
                [36,"chance","Chance"],
                [37,"property","Park Lane"],
                [38,"tax","Super Tax"],
                [39,"property","Mayfair"]
]

# define list of chance cards:
chance_cards = [
    ["advanceto","Advance to Go", 0,0],
    ["gotojail", "Go to Jail",10,0],
    ["advanceto","Advance to Trafalgar Square",24,0],
    ["advanceto","Advance to Mayfair", 39,0],
    ["advanceto","Advance to nearest Utility",12,28],
    ["advanceto","Advance to nearest Station",5,15,25,35],
    ["advanceto","Advance to Go", 0,0],
    ["gotojail","Go to Jail", 10,0],
    ["goback","Go back 3 spaces", -3,0],
    ["goback","Go back to Old Kent Road", 1,0],
    ["pay","Pay poor tax of £15", -15,0],
    ["receive","Your building loan matures, collect £150",150,0],
    ["receive","You have won a crossword competition, collect £100", 100,0],
    ["pay","You are elected Chairman of the Board of Directors, pay £50", -50,0],
    ["receive","Your stock dividend is £45", 45,0],
    ["repairs","Make general repairs to all your properties, for each house pay £25, for each hotel pay £100", -25,-100],
    ["pay","You have been assessed for street repairs, pay £40", -40,0],
    ["receive","Bank error in your favour, collect £200", 200,0],
    ["receive","You have won second prize in a beauty contest, collect £10", 10,0],
    ["receive","You inherit £100", 100,0],
    ["receive","From sale of stock you get £50", 50,0],
    ["jailfreecard","Get out of jail free", 0,0],
    ["pay","Pay school fees of £150", -150,0],
    ["receive","You have won first prize in a beauty contest, collect £10", 10,0],
    ["advanceto","Advance to Pall Mall", 11,0],
    ["advanceto","Advance to Trafalgar Square", 24,0],
    ["advanceto","Advance to Mayfair", 39,0],
    ["advanceto","Advance to nearest Utility", 12,28],
    ["advanceto","Advance to nearest Station", 5,15,25,35]
]

# define list of community chest cards:
community_chest_cards = [
    ["advanceto","Advance to Go", 0,0],
    ["gotojail", "Go to Jail",10,0],
    ["advanceto","Advance to Trafalgar Square",24,0],
    ["advanceto","Advance to Mayfair", 39,0],
    ["advanceto","Advance to nearest Utility",12,28],
    ["advanceto","Advance to nearest Station",5,15,25,35],
    ["advanceto","Advance to Go", 0,0],
    ["gotojail","Go to Jail", 10,0],
    ["goback","Go back 3 spaces", -3,0],
    ["goback","Go back to Old Kent Road", 1,0],
    ["pay","Pay poor tax of £15", -15,0],
    ["receive","Your building loan matures, collect £150",150,0],
    ["receive","You have won a crossword competition, collect £100", 100,0],
    ["pay","You are elected Chairman of the Board of Directors, pay £50", -50,0],
    ["receive","Your stock dividend is £45", 45,0],
    ["repairs","Make general repairs to all your properties, for each house pay £25, for each hotel pay £100", -25,-100],
    ["pay","You have been assessed for street repairs, pay £40", -40,0],
    ["receive","Bank error in your favour, collect £200", 200,0],
    ["receive","You have won second prize in a beauty contest, collect £10", 10,0],
    ["receive","You inherit £100", 100,0],
    ["receive","From sale of stock you get £50", 50,0],
    ["jailfreecard","Get out of jail free", 0,0],
    ["pay","Pay school fees of £150", -150,0],
    ["receive","You have won first prize in a beauty contest, collect £10", 10,0],
    ["advanceto","Advance to Pall Mall", 11,0],
    ["advanceto","Advance to Trafalgar Square", 24,0],
    ["advanceto","Advance to Mayfair", 39,0],
    ["advanceto","Advance to nearest Utility", 12,28],
    ["advanceto","Advance to nearest Station", 5,15,25,35]
]

pls = create_players(x)
b = create_board(propData, squares)
play_game(b, pls)
