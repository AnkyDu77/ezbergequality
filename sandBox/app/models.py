from app import db

class Traders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    traderID = db.Column(db.String(128), index=True, unique=True)
    userRegTime = db.Column(db.Float)
    cryptoAddress = db.Column(db.String(128), index=True, unique=True)
    nickname = db.Column(db.String(64))

    def __repr__(self):
        return '<Trader: {} || Cryptowallet: {} || Trader ID: {}>'.format(self.nickname, self.cryptoAddress, self.traderID)


class Strategies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strategyID = db.Column(db.Integer, index=True, unique=True)
    regTime = db.Column(db.Float)
    ush = db.Column(db.String(128), index=True)
    strategyName = db.Column(db.String(128))
    algoOpenness = db.Column(db.Integer)
    capitalCapacity = db.Column(db.Float)
    leverage = db.Column(db.Integer)

    def __repr__(self):
        return '<Strategy: {} || algoOpenness: {} || capitalCapacity: {}>'.format(self.strategyID, self.algoOpenness, self.capitalCapacity)

class Accounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strategyID = db.Column(db.Integer, index=True)
    timestamp = db.Column(db.Float)
    startDayBalance = db.Column(db.Float)
    onMargin = db.Column(db.Float)
    comissions = db.Column(db.Float)
    endDayBalance = db.Column(db.Float)

    def __repr__(self):
        return '<Account for strategy: {} || endDayBalance: {}>'.format(self.strategyID, self.endDayBalance)


class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Float)
    strategyID = db.Column(db.Integer, index=True)
    market = db.Column(db.String(64))
    symbol = db.Column(db.String(64))
    orderID = db.Column(db.String(128), index=True)
    direction = db.Column(db.String(64))
    orderType = db.Column(db.String(64))
    price = db.Column(db.Float)
    volume = db.Column(db.Float)
    timeInForce = db.Column(db.String(64))
    status = db.Column(db.String(64))
    attribute = db.Column(db.String(64))
    positionID = db.Column(db.String(128))

    def __repr__(self):
        return '<Order: {} || Strategy: {} || Direction {} || {} @ {}>'.format(self.orderID, self.strategyID, self.direction, self.volume, self.price)


class Positions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Float)
    strategyID = db.Column(db.Integer, index=True)
    market = db.Column(db.String(64))
    symbol = db.Column(db.String(64))
    direction = db.Column(db.String(64))
    openPrice = db.Column(db.Float)
    volume = db.Column(db.Float)
    liqPrice = db.Column(db.Float)
    urealisedPL = db.Column(db.Float)
    realisedPL = db.Column(db.Float)
    status = db.Column(db.Integer, index=True)
    positionID = db.Column(db.String(128), index=True)

    def __repr__(self):
        return '<Positions: {} || Strategy: {} || Direction {} || {} @ {} || liqPrice: {}>'.format(self.positionID, self.strategyID, self.direction, self.volume, self.openPrice, self.liqPrice)


class StrategiesIDs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Float)
    salt = db.Column(db.LargeBinary)
    hashKey = db.Column(db.LargeBinary)
    traderID = db.Column(db.String(128), index=True)
    

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Float)
    strategyID = db.Column(db.Integer, index=True)
    algoOpenness = db.Column(db.Float)
    maxCapCapacity = db.Column(db.Float)
    winRate = db.Column(db.Float)
    profitability = db.Column(db.Float)
    marketBeat = db.Column(db.Float)
    resultRate = db.Column(db.Float)
