# SPDX-License-Identifier: GPL-3.0-only
# Lecture adaptee de SoulMemory, Frank van der Stam ; adaptation Python 2026-10-02.
from .i18n import tr, translate_status
import struct

def locate_flags(reader):
    import re

    def pattern_regex(pattern):
        return re.compile(b''.join((b'.' if token == '?' else re.escape(bytes([int(token, 16)])) for token in pattern.split())), re.DOTALL)
    header = reader.read(reader.base, 4096)
    pe = struct.unpack_from('<I', header, 60)[0]
    if header[pe:pe + 4] != b'PE\x00\x00':
        raise ValueError('Executable PE invalide')
    count = struct.unpack_from('<H', header, pe + 6)[0]
    optional = struct.unpack_from('<H', header, pe + 20)[0]
    if not 1 <= count <= 128:
        raise ValueError('Nombre de sections PE incoherent')
    table = reader.read(reader.base + pe + 24 + optional, count * 40)
    pattern = pattern_regex('44 89 7c 24 28 4c 8b 25 ? ? ? ? 4d 85 e4')
    matches = set()
    for i in range(count):
        section = table[i * 40:(i + 1) * 40]
        size, rva = struct.unpack_from('<II', section, 8)
        flags = struct.unpack_from('<I', section, 36)[0]
        if not flags & 536870912:
            continue
        if rva + size > reader.size:
            raise ValueError('Section executable incoherente')
        previous = b''
        for offset in range(0, size, 1024 * 1024):
            block = reader.read(reader.base + rva + offset, min(1024 * 1024, size - offset))
            chunk = previous + block
            origin = reader.base + rva + offset - len(previous)
            matches.update((origin + match.start() for match in pattern.finditer(chunk)))
            previous = chunk[-64:]
    if len(matches) != 1:
        raise ValueError(f'Signature complete event_flags : {len(matches)} correspondances, lecture refusee')
    address = next(iter(matches))
    instruction = reader.read(address, 12)
    return address + 12 + struct.unpack_from('<i', instruction, 8)[0]

def flag(reader, manager, identifier):
    divisor = reader.integer(manager + 28)
    if not 1 <= divisor <= 1000000:
        raise ValueError('Diviseur de flags invalide ou non initialise')
    category, remainder = divmod(identifier, divisor)
    header = reader.ptr(manager + 56)
    node = reader.ptr(header + 8)
    candidate = header
    seen = set()
    for _ in range(128):
        sentinel = reader.read(node + 25, 1)[0]
        if sentinel == 1:
            break
        if sentinel != 0 or node in seen:
            raise ValueError('Arbre de flags incoherent')
        seen.add(node)
        key = reader.integer(node + 32)
        if key < category:
            node = reader.ptr(node + 16)
        else:
            candidate = node
            node = reader.ptr(node)
    else:
        raise ValueError('Parcours de flags trop long')
    if candidate == header or reader.integer(candidate + 32) != category:
        raise ValueError('Categorie absente : etat inconnu, pas faux')
    mode = reader.integer(candidate + 40)
    if mode == 1:
        stride = reader.integer(manager + 32)
        index = reader.integer(candidate + 48)
        if stride <= 0 or index < 0:
            raise ValueError('Stockage indexe invalide')
        storage = reader.ptr(manager + 40) + stride * index
    elif mode == 2:
        raise ValueError('Categorie sans stockage lisible')
    else:
        storage = reader.ptr(candidate + 48)
    byte = reader.read(storage + (remainder >> 3), 1)[0]
    return bool(byte & 1 << 7 - (remainder & 7))

# FLAG_BATCH_CYCLE_V1 - caches invalides entre deux cycles.
import time as _batch_time

class FlagBatch:
    def __init__(self, reader, manager, deadline=None, clock=None):
        self.reader=reader;self.manager=manager;self.clock=clock or _batch_time.monotonic;self.deadline=deadline
        self.nodes={};self.groups={};self.bytes={};self.indexed=None
        self._check()
        self.divisor=reader.integer(manager+28)
        if not 1<=self.divisor<=1000000: raise ValueError('Diviseur de flags invalide ou non initialise')
        self.header=reader.ptr(manager+56);self.root=reader.ptr(self.header+8)
    def _check(self):
        if self.deadline is not None and self.clock()>self.deadline: raise ValueError('Cycle de flags trop lent - attribution suspendue')
    def _node(self, address):
        self._check()
        if address not in self.nodes:
            sentinel=self.reader.read(address+25,1)
            if len(sentinel)!=1: raise ValueError('Lecture de noeud incomplete')
            sentinel=sentinel[0]
            if sentinel not in (0,1): raise ValueError('Arbre de flags incoherent')
            if sentinel==1: self.nodes[address]=(1,None,None,None)
            else: self.nodes[address]=(0,self.reader.integer(address+32),self.reader.ptr(address),self.reader.ptr(address+16))
        return self.nodes[address]
    def _group(self, category):
        if category in self.groups: return self.groups[category][0]
        node=self.root;candidate=self.header;seen=set()
        for _ in range(128):
            sentinel,key,left,right=self._node(node)
            if sentinel==1: break
            if node in seen: raise ValueError('Arbre de flags incoherent')
            seen.add(node)
            if key<category: node=right
            else: candidate=node;node=left
        else: raise ValueError('Parcours de flags trop long')
        if candidate==self.header or self._node(candidate)[1]!=category: raise ValueError('Categorie absente : etat inconnu, pas faux')
        mode=self.reader.integer(candidate+40)
        if mode==1:
            if self.indexed is None:
                stride=self.reader.integer(self.manager+32);base=self.reader.ptr(self.manager+40)
                if stride<=0: raise ValueError('Stockage indexe invalide')
                self.indexed=(stride,base)
            index=self.reader.integer(candidate+48)
            if index<0: raise ValueError('Stockage indexe invalide')
            storage=self.indexed[1]+self.indexed[0]*index;detail=index
        elif mode==2: raise ValueError('Categorie sans stockage lisible')
        else: storage=self.reader.ptr(candidate+48);detail=storage
        self.groups[category]=(storage,candidate,mode,detail)
        return storage
    def get(self, identifier):
        self._check()
        if type(identifier) is not int or not 0<=identifier<=4294967295: raise ValueError('Identifiant de flag invalide')
        category,remainder=divmod(identifier,self.divisor);address=self._group(category)+(remainder>>3)
        if address not in self.bytes:
            data=self.reader.read(address,1)
            if len(data)!=1: raise ValueError('Lecture de flag incomplete')
            self.bytes[address]=data[0]
        return bool(self.bytes[address] & (1 << (7-(remainder&7))))
    def verify(self):
        self._check()
        r=self.reader
        if r.integer(self.manager+28)!=self.divisor or r.ptr(self.manager+56)!=self.header or r.ptr(self.header+8)!=self.root:
            raise ValueError('Structure de flags en transition - attribution suspendue')
        if self.indexed is not None and (r.integer(self.manager+32),r.ptr(self.manager+40))!=self.indexed:
            raise ValueError('Stockage de flags en transition - attribution suspendue')
        for category,(_,node,mode,detail) in self.groups.items():
            self._check()
            if r.integer(node+32)!=category or r.integer(node+40)!=mode:
                raise ValueError('Categorie de flags en transition - attribution suspendue')
            current=r.integer(node+48) if mode==1 else r.ptr(node+48)
            if current!=detail: raise ValueError('Stockage de categorie en transition - attribution suspendue')
        if flag(r,self.manager,6000) is not False or flag(r,self.manager,6001) is not True:
            raise ValueError('Flags de controle incorrects')
        self._check()
