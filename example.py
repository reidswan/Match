from match.dsl import MatchDSL

m = MatchDSL()

# square brackets denote an exact match
name_match = m['name']
# similarly, call .MATCH
name_match_2 = m.MATCH('name')

# calling a matcher to check for a match
result = name_match('name')
result2 = name_match_2('name')
assert(result.get_match() == result2.get_match())

# specify a value range
(m < ('a', 'z')) // 'lower case'
m.BETWEEN('A', 'Z') // 'upper_case'

# using the C-style line comment saves the matcher for later referencing
m.REF('lower case')
# if the name is a valid python identifier, it can be referenced using dot notation
m.upper_case

# there are three ways of naming a match to allow for referencing later
m['(']//'open_bracket'
m[')']^'close_bracket'
m.MATCH(':').STORE('colon')

# matches can be sequenced 
m['a'].THEN(m['b']).THEN(m['c'])
m['a'] + m['b'] + m['c']

# or optioned
m['a'].OR(m['b']).OR(m['c'])
m['a'] | m['b'] | m['c']

# there are three types of repetition:
## AGAIN multiplies by 2
once_again = m['a'].AGAIN()
twice_again = once_again.AGAIN()
assert(once_again('aa').get_match() == 'aa')
assert(twice_again('aaaa').get_match() == 'aaaa')

## REPEAT()/unary + matches 0 or more repetitions
m['a'].REPEAT()//'any'
assert(m.any('').successful)
assert((+m['a'])('aaa').remainder == '')

## REPEAT(n) / *n matches exactly n repetitions
(m['a']*2) // 'a_2'
m['a'].REPEAT(3).STORE('a_3')
assert(m.a_2('aaa').get_match() == 'aa') # this shows also that matches are greedy
assert(not m.a_3('aa').successful)
assert(m.a_3('aaa').successful)

# Negation (.NOT, -) matches the first character if the matcher it's negating fails to match
-m['a'] //'not_a'
assert(not m.not_a('a').successful)
assert(m.not_a('b').successful)

-m['abc'].AGAIN() // 'not_double_abc'
assert(len(m.not_double_abc('abcab').get_match()) == 1)

# make a match optional:
~m['a'] // 'optionally_a'
m['b'].OPTIONAL()
assert(m.optionally_a('b').successful)
assert(m.optionally_a('a').successful)


# example: 
# arithmetic sum
m = MatchDSL() # just resetting
(m < ('1', '9'))                                    // 'non_zero_digit'
(m.non_zero_digit | m['0'])                         // 'digit'
(m.non_zero_digit + +m.digit)                       // 'positive_integer'
(m['-'] + m.positive_integer)                       // 'negative_integer'
(m['0'] | m.positive_integer | m.negative_integer)  // 'integer'
# integer can be equivalently specified as:
(m['0'] | (~m['-'] + m.positive_integer))           // 'integer_v2'
(+m[' '])                                           // 'whitespace'
(m.whitespace + m.integer + m.whitespace)           // 'w_integer'
(m.w_integer + +(m['+'] + m.w_integer))             // 'sum'
# m.sum will now match arithmetic sums!

# we can also do this in a pseudo one liner...
# using \ to break for "readability"
n = MatchDSL()
n.BETWEEN('1', '9').STORE('non_zero_digit').OR(n.MATCH('0')).STORE('digit')\
    .REF('non_zero_digit').THEN(n.digit.REPEAT()).STORE('positive_integer')\
    .MATCH('-').THEN(n.positive_integer).STORE('negative_integer')\
    .MATCH('0').OR(n.positive_integer.OR(n.negative_integer))\
    .STORE('integer')\
    .MATCH(' ').REPEAT().STORE('whitespace')\
    .THEN(n.integer.THEN(n.whitespace)).STORE('w_integer')\
    .THEN(n.MATCH('+').THEN(n.w_integer).REPEAT()).STORE('sum')
# et voila, n.sum matches arithmetic sums

# once more for luck?
_ = MatchDSL()
((((+((_['0']|(~_['-']+(((((_<('1','9'))//'nzd')|_['0'])//'d').nzd++_.d)))//'int')[' ']//'ws')+_.int+_.ws)//'wint')++(_['+']+_.wint))//'sum'
