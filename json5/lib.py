# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collections
import re
import json
import sys

from .parser import Parser


_is_python2 = sys.version_info[0] < 3
if _is_python2:
    # pylint: disable=redefined-builtin
    str = unicode


def load(fp, **kwargs):
    """Deserialize ``fp`` (a ``.read()``-supporting file-like object
    containing a JSON document) to a Python object."""
    return _Decoder(**kwargs).loads(fp.read())


def loads(s, **kwargs):
    """Deserialize ``s`` (a ``str`` or ``unicode`` instance containing a
    JSON5 document) to a Python object."""
    return _Decoder(**kwargs).loads(s)


class _Decoder(object):

    def __init__(self, encoding=None, cls=None, object_hook=None,
                 parse_float=None, parse_int=None, parse_constant=None,
                 object_pairs_hook=None):
        assert cls is None, 'Custom decoders are not supported'

        self.encoding = encoding or 'utf-8'
        self.cls = cls
        self.parse_float = parse_float or float
        self.parse_int = parse_int or int
        self.parse_constant = parse_constant or self.parse_constant
        self.object_pairs_hook = object_pairs_hook
        if object_pairs_hook:
            self.object_pairs_hook = object_pairs_hook
        elif object_hook:
            self.object_pairs_hook = lambda pairs: object_hook(dict(pairs))
        else:
            self.object_pairs_hook = dict

    def parse_constant(self, s):
        return float(s.replace('Infinity', 'inf').replace('NaN', 'nan'))

    def loads(self, s):
        if _is_python2:
            decodable_type = type('')
        else:
            decodable_type = type(b'')
        if isinstance(s, decodable_type):
            s = s.decode(self.encoding)

        if not s:
            raise ValueError('Empty strings are not legal JSON5')

        parser = Parser(s, '<string>')
        ast, err = parser.parse()
        if err:
            raise ValueError(err)

        return self.walk(ast)

    def walk(self, ast_node):
        node_type, node_val = ast_node
        if node_type in ('null', 'true', 'false', 'string'):
            return node_val
        elif node_type == 'number':
            if node_val.startswith('0x') or node_val.startswith('0X'):
                return self.parse_int(node_val, base=16)
            elif '.' in node_val or 'e' in node_val or 'E' in node_val:
                return self.parse_float(node_val)
            elif 'Infinity' in node_val or 'NaN' in node_val:
                return self.parse_constant(node_val)
            else:
                return self.parse_int(node_val)
        elif node_type == 'object':
            pairs = [(key, self.walk(val)) for key, val in node_val]
            return self.object_pairs_hook(pairs)
        elif node_type == 'array':
            return [self.walk(el) for el in node_val]
        else:  # pragma: no cover
            raise Exception('unknown ast node: ' + repr(ast_node))



def dumps(obj, **kwargs):
    """Serialize ``obj`` to a JSON5-formatted string."""
    compact = kwargs.pop('compact', False)
    as_json = kwargs.pop('as_json', not compact)
    if as_json:
        return json.dumps(obj, **kwargs)
    else:
        return _Encoder(**kwargs).dumps(obj)


def dump(obj, fp, **kwargs):
    """Serialize ``obj`` to a JSON5-formatted stream to ``fp`` (a ``.write()``-
    supporting file-like object)."""
    fp.write(dumps(obj, **kwargs))


squote = "'"
dquote = '"'
bslash = '\\'


class _Encoder(object):

    def __init__(self, skipkeys=False, ensure_ascii=True,
                 check_circular=True, allow_nan=True,
                 cls=None, indent=None, separators=None,
                 encoding='utf-8', default=None,
                 sort_keys=False):
        assert cls is None, 'Custom encoders are not supported'

        self.skipkeys = skipkeys
        self.ensure_ascii = ensure_ascii
        self.check_circular = check_circular
        self.allow_nan = allow_nan
        self.indent = indent
        self.encoding = encoding
        self.default = default or self._default
        self.sort_keys = sort_keys

        if separators:
          self._comma, self._colon = separators
        else:
          self._comma, self._colon = (', ', ': ')
        self._notletter = re.compile('\W')
        self._seen_objs = set()
        self._valid_key_types = [str, int, float, bool, type(None)]
        if _is_python2:
            self._valid_key_types.extend([long, type('')])
        self._indent_level = 0

    def _default(self, obj):
        raise TypeError(obj)

    def _esc_key(self, k):
        if self._notletter.search(k):
            if not squote in k:
                return squote + self._esc_str(k, esc_dquote=False) + squote
            else:
                return dquote + self._esc_str(k, esc_squote=False) + dquote
        else:
            return k

    def _esc_str(self, s, esc_squote=True, esc_dquote=True):
        if not self.ensure_ascii:
            return s
        chars = []
        for ch in s:
            chars.append(self._esc_char(ch, esc_squote, esc_dquote))
        return ''.join(chars)

    def _esc_char(self, ch, esc_squote, esc_dquote):
        o = ord(ch)
        if ch == dquote and esc_dquote:
            return bslash + dquote
        if ch == squote and esc_squote:
            return bslash + squote
        elif 32 <= o < 128:
            return ch
        else:
            return '\\u%04x' % o

    def dumps(self, obj):
        t = type(obj)
        if obj is True:
            return 'true'
        elif obj is False:
            return 'false'
        elif obj is None:
            return 'null'
        elif t == type('') or t == type(u''):
            has_single_quote = "'" in obj
            if not has_single_quote:
                return squote + self._esc_str(obj, esc_dquote=False) + squote
            else:
                return dquote + self._esc_str(obj, esc_squote=False) + dquote
        elif t is float:
            if not self.allow_nan and math.isnan(obj) or math.isinf(obj):
                raise ValueError(obj)
        elif t is int:
            return str(obj)
        elif t is dict:
            if self.check_circular:
                if id(obj) in self._seen_objs:
                    raise ValueError(obj)
                self._seen_objs.add(id(obj))

            keys = obj.keys()
            if self.sort_keys:
                keys = sorted(keys)
            num_keys = len(keys) - 1

            self._indent_level += 1
            if self.indent is not None:
                indent += '\n' + ' ' * self.indent * self.indent_level
            else:
                indent = ''

            s = '{' + indent
            for i, k in enumerate(keys):
                if type(k) not in self._valid_key_types:
                    if self.skipkeys:
                        continue
                    raise TypeError(k)
                s += self._esc_key(k) + self._colon + self.dumps(obj[k])
                if i < num_keys:
                    s += self._comma + indent
            s += '}'

            self._indent_level -= 1
            return s

        elif t is list:
            if self.check_circular:
                if id(obj) in self._seen_objs:
                    raise ValueError(obj)
                self._seen_objs.add(id(obj))
            num_els = len(obj) - 1

            self._indent_level += 1
            if self.indent is not None:
                indent += '\n' + ' ' * self.indent * self.indent_level
            else:
                indent = ''

            s = '[' + indent
            for i, el in enumerate(obj):
                s += self.dumps(el)
                if i < num_els:
                    s += self._comma + indent
            s += ']'

            self._indent_level -= 1
            return s
        else:
            self._default(obj)
