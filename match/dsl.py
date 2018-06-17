from match.matchers import LiteralMatcher, SequenceMatcher,\
    RangeMatcher, AnyMatcher, RefMatcher, RepeatedMatcher,\
    NotMatcher, OptionalMatcher

class MatchDSL:
    def __init__(self):
        self.registry = {}
        self.last = None
    
    def _new(self, matcher):
        m = MatchDSL()
        m.registry = self.registry
        m.last = matcher
        return m

    def __call__(self, source):
        if not self.last:
            raise ValueError("Attempting to match when no matcher defined")
        return self.last.match(source)
    
    def MATCH(self, literal):
        return self._new(LiteralMatcher('', literal))

    def STORE(self, name):
        self.registry[name] = self.last
        self.last.name = name
        return self

    def REF(self, name):
        return self._new(self.registry[name])

    def THEN(self, seq):
        if type(seq) is MatchDSL:
            seq = seq.last
        return self._new(SequenceMatcher('', self.last, seq))
    
    def BETWEEN(self, lower, upper):
        return self._new(RangeMatcher('', lower, upper))
    
    def OR(self, alt):
        if type(alt) is MatchDSL:
            alt = alt.last
        return self._new(AnyMatcher('', self.last, alt))

    def NOT(self):
        return self._new(NotMatcher('', self.last))

    def AGAIN(self):
        return self.THEN(self)

    def REPEAT(self, n=None):
        if not n:
            return self._new(RepeatedMatcher('', self.last))
        return self._new(SequenceMatcher('', *[self.last]*n))

    def OPTIONAL(self):
        return self._new(OptionalMatcher('', self.last))

    def __getattr__(self, name):
        return self.REF(name)

    def __xor__(self, name):
        return self.STORE(name)

    def __floordiv__(self, name):
        return self.STORE(name)

    def __getitem__(self, literal):
        return self.MATCH(literal)

    def __add__(self, seq):
        return self.THEN(seq)

    def __lt__(self, bounds):
        return self.BETWEEN(*bounds)
    
    def __or__(self, alt):
        return self.OR(alt)
    
    def __mul__(self, n):
        return self.REPEAT(n)

    def __neg__(self):
        return self.NOT()

    def __pos__(self):
        return self.REPEAT()

    def __invert__(self):
        return self.OPTIONAL()
    