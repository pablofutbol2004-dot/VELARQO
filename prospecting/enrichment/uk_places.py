"""UK place names that must never count as a company's "distinctive" name
word: "Perthshire Glazing" vs a competitor's site that mentions Perthshire,
"South Liverpool Windows" vs any Liverpool installer. Counties, regions and
the larger towns; the company's own town is added per lead."""

COUNTIES_AND_REGIONS = {
    "aberdeenshire", "anglesey", "angus", "antrim", "argyll", "armagh", "avon", "ayrshire", "bedfordshire",
    "berkshire", "berwickshire", "borders", "buckinghamshire", "bucks", "caithness", "cambridgeshire", "cambs",
    "carmarthenshire", "ceredigion", "cheshire", "clackmannanshire", "cleveland", "clwyd", "conwy", "cornwall",
    "cotswold", "cotswolds", "cumbria", "denbighshire", "derbyshire", "devon", "dorset", "down", "dumfries",
    "dumfriesshire", "dunbartonshire", "durham", "dyfed", "essex", "fermanagh", "fife", "flintshire",
    "galloway", "glamorgan", "gloucestershire", "glos", "gwent", "gwynedd", "hampshire", "hants",
    "herefordshire", "hertfordshire", "herts", "highland", "highlands", "humberside", "inverclyde",
    "kent", "kincardineshire", "kinross", "lanarkshire", "lancashire", "lancs", "leicestershire", "leics",
    "lincolnshire", "lincs", "lothian", "merseyside", "middlesex", "midlands", "midlothian", "monmouthshire",
    "moray", "norfolk", "northamptonshire", "northants", "northumberland", "nottinghamshire", "notts",
    "orkney", "oxfordshire", "oxon", "pembrokeshire", "perthshire", "powys", "renfrewshire", "rutland",
    "shetland", "shropshire", "somerset", "staffordshire", "staffs", "stirlingshire", "suffolk", "surrey",
    "sussex", "tayside", "tyne", "tyneside", "tyrone", "wales", "warwickshire", "wearside", "wiltshire",
    "wilts", "worcestershire", "worcs", "wrexham", "yorkshire", "yorks", "scotland", "england", "britain",
    "british", "anglia", "pennine", "pennines", "peak", "lakes", "lakeland", "chiltern", "chilterns",
    "solent", "severn", "thames", "mersey", "clyde", "forth", "humber", "wessex", "mercia", "northumbria",
}

TOWNS = {
    "aberdeen", "aldershot", "altrincham", "andover", "ashford", "aylesbury", "ayr", "banbury", "bangor", "barnet",
    "barnsley", "barrow", "basildon", "basingstoke", "bath", "bedford", "belfast", "birkenhead", "birmingham",
    "blackburn", "blackpool", "bolton", "bournemouth", "bracknell", "bradford", "braintree", "brighton", "bristol",
    "bromley", "burnley", "burton", "bury", "cambridge", "canterbury", "cardiff", "carlisle", "chatham",
    "chelmsford", "cheltenham", "chester", "chesterfield", "chichester", "colchester", "coventry", "crawley",
    "crewe", "croydon", "darlington", "derby", "doncaster", "dover", "dudley", "dundee", "dunfermline",
    "eastbourne", "edinburgh", "enfield", "exeter", "falkirk", "farnborough", "gateshead", "glasgow",
    "gloucester", "grimsby", "guildford", "halifax", "harlow", "harrogate", "hartlepool", "hastings",
    "hemel", "hereford", "harrow", "high", "wycombe", "huddersfield", "hull", "ilford", "inverness", "ipswich",
    "kendal", "kettering", "kidderminster", "kilmarnock", "kingston", "kirkcaldy", "lancaster", "leeds",
    "leicester", "lincoln", "liverpool", "livingston", "london", "londonwide", "luton", "maidstone",
    "manchester", "mansfield", "margate", "middlesbrough", "milton", "keynes", "newcastle", "newport",
    "northampton", "norwich", "nottingham", "nuneaton", "oldham", "oxford", "paisley", "perth", "peterborough",
    "plymouth", "poole", "portsmouth", "preston", "reading", "redditch", "rochdale", "romford", "rotherham",
    "rugby", "runcorn", "salford", "salisbury", "scarborough", "scunthorpe", "sheffield", "shrewsbury",
    "slough", "solihull", "southampton", "southend", "southport", "stafford", "stevenage", "stirling",
    "stockport", "stockton", "stoke", "sunderland", "sutton", "swansea", "swindon", "taunton", "telford",
    "torquay", "truro", "wakefield", "walsall", "warrington", "watford", "wigan", "winchester", "woking",
    "wolverhampton", "worcester", "worthing", "wrexham", "york", "yeovil", "wembley", "wetherby",
}

PLACE_WORDS = COUNTIES_AND_REGIONS | TOWNS
