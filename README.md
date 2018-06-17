# Match
Match is a RegEx-like DSL embedded in Python

This is actual, runnable Python defining a Match pattern:
```
((((+(_['0']|(~_['-']+((((((_<('1','9'))//'nzd')|_['0'])//'d').nzd++_.d)))//'int')[' ']//'ws')+_.int+_.ws)//'wint')++(_['+']+_.wint))//'sum'
```

Curious? See [example.py](example.py)

## Syntax

The following table provides an overview of Match's syntax. See [example.py](example.py) to see it in action 

| Function      | Operator      | Action|
| ------------- |-------------  | ----- |
| `m.MATCH('a')` | `m['a']` | Match the supplied string exactly|
| `m.BETWEEN('a', 'b')` | `m < ('a', 'b')` | Match a character in the range from 'a' to 'b'|
| `m.THEN(x)`| `m + x`| Perform the match defined by `m`; if it succeeds, perform the match defined by `x`|
| `m.OR(x)` | `m \| x` | Perform the match defined by `m`; if it fails, backtrack and perform the match defined by `x`|
| `m.NOT()` | `-m` | Match the first character of the string only if m fails to match |
| `m.REPEAT()` | `+m` | Perform the match defined by `m` 0 or more times |
| `m.REPEAT(n)` | `m*n` | Perform the match defined by `m` exactly `n` times |
| `m.AGAIN()` | - | Repeat `m` |
| `m.OPTIONAL(x)` | `~m` | Optionally perform the match defined by `m`|
| `m.STORE('name')` | `m//'name'` | Bind the match `m` to the name `'name'` |
| `m.REF('name')` | `m.name` | Access the match bound to the name `name` |

### Notes:
- `AGAIN()` is exponential -- for example, `m.AGAIN().AGAIN()` will peform `m`'s match four times, and `m.AGAIN().AGAIN().AGAIN()` eight.

- The dot notation for bound name referencing only works if `name` is a valid Python expression, whereas `REF` should work for all strings
