from logging import getLogger
from typing import List, TypeVar
from abc import ABC, abstractmethod

logger = getLogger(__name__)

class Match:
    """
    Container returned by matchers with details of the match
    Treated like an n-ary tree -- children are the elements of the 
    tokens list, with instances of Match acting as nodes and
    strings acting as the leaves
    """
    def __init__(self, successful: bool, name: str, tokens: list, remainder: str):
        """
        :param successful: flag indicating if the match was successful
        :param name: the name of the matching function that was run to achieve this Match
        :param tokens: list of tokens matched by the Matcher (str or Match)
        :param remainder: the contents of the string following the match
        """
        self.successful = successful
        self.name = name
        self.tokens = tokens
        self.remainder = remainder

    def __repr__(self, indent=0):
        token_repr = "\n".join([t.__repr__(indent+1) if isinstance(t, Match) else t.__repr__() for t in self.tokens])
        remainder = self.remainder.__repr__() 
        remainder = remainder if len(remainder) <= 13 else self.remainder[:10] + "...'"
        return (
            "{indent}{{name:{name}, successful:{successful}, remainder:{remainder}, tokens:[\n{indent}{tokens}\n{indent}]}}"\
            .format(name=self.name, successful=self.successful,
                    remainder=remainder, tokens=token_repr, 
                    indent=' '*indent)
        )

    def __str__(self, indent=0):
        if self.successful:
            own_description = "{indent}[{name}]{{\n{children}\n{indent}}}" 
        else:
            own_description = "{indent}[{name}]{{}}"
        children_repr = "\n".join([
            t.__str__(indent+1) if isinstance(t, Match) 
            else "{indent}{elem}".format(indent=" "*(indent+1), elem=t.__repr__())
            for t in self.tokens
        ])
        return own_description.format(name=self.name, children=children_repr, indent=" "*indent)

    def get_match(self):
        return "".join([
            t if type(t) is str 
            else t.get_match()
            for t in self.tokens
        ])
    

class Matcher(ABC):
    @abstractmethod
    def match(self, source: str)-> Match:
        raise NotImplementedError("Derived classes must override the match function")

    def __call__(self, source):
        return self.match(source)

class LiteralMatcher(Matcher):
    """
    Matches exactly the supplied literal
    """
    def __init__(self, name: str, literal: str, case_sensitive: bool=True):
        """
        :param name: string to identify this matcher
        :param literals: the literal string to match
        :param case_sensitive: (default True) whether matches must match case
        """
        self.name = name
        if not literal:
            logger.warning("Matching on an empty literal in {}".format(name))
        self.literal = literal
        self.case_sensitive = case_sensitive

    def match(self, source: str)-> Match:
        _source = source if self.case_sensitive else source.lower()
        _literal = self.literal if self.case_sensitive else self.literal.lower()
        if _source.startswith(_literal):
            return Match(True, self.name, [self.literal], source[len(self.literal):])
        return Match(False, self.name, [], source)


class RangeMatcher(Matcher):
    """
    Matches single characters that fall in the given ranges
    """
    def __init__(self, name: str, lower: str, upper: str, lower_inclusive: bool=True, upper_inclusive: bool=True):
        """
        :param name: string identifying this matcher
        :param lower: the lower bounding char of the range
        :param upper: the upper bounding char of the range
        :param lower_inclusive: (default True) flag indicating whether the match is inclusive on the lower bound
        :param upper_inclusive: (default True) flag indicating whether the match is inclusive on the upper bound
        """
        if len(lower) != 1:
            raise ValueError("RangeMatcher requires a single character lower bound")
        if len(upper) != 1:
            raise ValueError("RangeMatcher requires a single character upper bound")
        self.name = name
        self.lower = lower
        self.upper = upper
        self.lower_inclusive = lower_inclusive
        self.upper_inclusive = upper_inclusive

        self.lbound = ord(lower) + (0 if lower_inclusive else 1)
        self.ubound = ord(upper) - (0 if upper_inclusive else 1)
        self.range_size = self.ubound - self.lbound
        if self.range_size <= 0:
            logger.warning("RangeMatcher {} has empty range".format(name))
    
    def match(self, source: str)-> Match:
        if not source:
            return Match(False, self.name, [], source)
        head = source[0]
        if self.lbound <= ord(head) <= self.ubound:
            return Match(True, self.name, [head], source[1:])
        else:
            return Match(False, self.name, [], source)
    
    def __len__(self):
        return self.range_size


class OptionalMatcher(Matcher):
    """
    Optionally match the given matcher
    """
    def __init__(self, name: str, matcher: List[Matcher]):
        self.name = name
        self.matcher = matcher

    def match(self, source: str):
        result = self.matcher.match(source)
        if result.successful:
            return Match(True, self.name, [result], result.remainder)
        return Match(True, self.name, [], source)


class AnyMatcher(Matcher):
    """
    Match one of a number of Matchers; returns the first successful Match
    """
    def __init__(self, name: str, *matchers: List[Matcher]):
        """
        :param name: string to identify this matcher
        :param matchers: a list of matchers; precedence of match based on list order
        """
        self.name = name
        if not matchers:
            logger.warning("No matchers provided to AnyMatcher {}".format(name))
        self.matchers = matchers
    
    def extend(self, matcher: Matcher):
        """
        Mutates the current AnyMatcher by providing an additional option
        :param matcher: the matcher to extend by
        """
        self.matchers = list(self.matchers) + [matcher]

    def match(self, source: str)-> Match:
        for matcher in self.matchers:
            result = matcher.match(source)
            if result.successful:
                return Match(True, self.name, [result], result.remainder)
        return Match(False, self.name, [], source)


class SequenceMatcher(Matcher):
    """
    Matches the supplied Matchers in sequence; fails if any of them fail
    """
    def __init__(self, name: str, *matchers: List[Matcher]):
        """
        :param name: string to identify this matcher
        :param matchers: the matchers to match sequentially
        """
        self.name = name
        if not matchers:
            logger.warning("Empty matchers supplied to SequenceMatcher {}".format(name))
        self.matchers = matchers

    def extend(self, matcher: Matcher):
        """
        Mutates the current SequenceMatcher by extending the sequence 
        :param matcher: the matcher to extend by
        """
        self.matchers = list(self.matchers) + [matcher]

    def match(self, source: str)-> Match:
        src = source
        matched = []
        for matcher in self.matchers:
            result = matcher.match(src)
            if not result.successful:
                return Match(False, self.name, [], source)
            src = result.remainder
            matched.append(result)
        return Match(True, self.name, matched, src)


class RepeatedMatcher(Matcher):
    """
    Matches 0 or more times on the given matcher
    """
    def __init__(self, name: str, matcher: Matcher):
        """
        :param name: string to identify this matcher
        :param matcher: the matcher which must match 0 or more times
        """
        self.name = name
        if type(matcher) is RepeatedMatcher:
            raise ValueError("Directly nesting RepeatedMatchers will result in infinite looping")
        self.matcher = matcher

    def match(self, source: str)-> Match:
        loop_watch = False
        matched = []
        src = source
        while len(src) > 0:
            result = self.matcher.match(src)
            if result.successful:
                if result.remainder == src:
                    if not loop_watch:
                        logger.warning("{} successfully matched without consuming")
                        loop_watch = True
                    else:
                        raise Exception("Infinite loop detected in {}".format(self.name))
                else:
                    loop_watch = False
                matched.append(result)
                src = result.remainder
            else: 
                break
        return Match(True, self.name, matched, src)

class RefMatcher(Matcher):
    """
    Refers to a matcher in a registry by name 
    """
    def __init__(self, ref_name: str, registry: dict):
        self.registry = registry
        self.ref_name = ref_name

    def match(self, source: str)-> Match:
        return self.registry[self.ref_name].match(source)

class NotMatcher(Matcher):
    """
    If the provided matcher fails, this succeeds, taking the first character as its token
    """
    def __init__(self, name: str, matcher: Matcher):
        self.name = name
        self.matcher = matcher

    def match(self, source: str)-> Match:
        if not source:
            return Match(False, self.name, '', '')
        result = self.matcher.match(source)
        if not result.successful:
            return Match(True, self.name, [source[0]], source[1:])
        return Match(False, self.name, '', source)
