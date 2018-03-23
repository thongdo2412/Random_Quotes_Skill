# -*- coding: UTF-8 -*-

# Just importing Forsimatic class
from randomquotes import Forismatic

# Initializing manager
f = Forismatic()

# Getting Quote object & printing quote and author
q = f.get_quote()
# print '%s by %s' % (q.quote, q.author)
print("%s by %s" % (q.quote,q.author))
