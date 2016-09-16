from datetime import datetime

import pytest
import sqlalchemy as sa

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

from sqlalchemy_norm import Normalizable


@pytest.fixture
def User(Base):
    class User(Base, Normalizable):
        __tablename__ = 'users'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
        nickname = sa.Column(sa.String)
        point = sa.Column(sa.Integer)
        created_at = sa.Column(sa.DateTime)

        primary_address = relationship("Address", uselist=False)

        __includes__ = ['addresses']

        @property
        def display_name(self):
            return "%s (%s)" % (self.nickname, self.name)

        def __init__(self, name, created_at):
            self.name = name
            self.created_at = created_at

    return User

@pytest.fixture
def Address(Base):
    class Address(Base, Normalizable):
        __tablename__ = 'addresses'
        id = sa.Column(sa.Integer, primary_key=True)
        street = sa.Column(sa.String)
        suburb = sa.Column(sa.String)
        state = sa.Column(sa.String)
        country = sa.Column(sa.String)
        postcode = sa.Column(sa.String)

        user_id = sa.Column(sa.Integer, ForeignKey('users.id'))
        user = relationship("User", backref=backref('addresses', order_by=id))

        def __init__(self, street=None, suburb=None,
                     state=None, country=None, postcode=None):
            self.street = street
            self.suburb = suburb
            self.state = state
            self.country = country
            self.postcode = postcode

    return Address

@pytest.fixture
def UserWithinAddresses(User, Address):
    me = User("Edward", datetime.now())

    addr1 = Address(
        street = '100 Flinders Ave',
        suburb = 'Melburne',
        state = 'Victoria',
        country = 'Australia',
        postcode = '3000'
    )

    addr2 = Address(
        street = '20 Albert Ave',
        suburb = 'South Melbourne',
        state = 'Victoria',
        country = 'Australia',
        postcode = '3205'
    )

    me.addresses = [ addr1, addr2 ]
    me.primary_address = addr1
    return me


class TestDotNotation():
    def test_type(self, UserWithinAddresses):
        norm = UserWithinAddresses.vars()
        assert isinstance(norm, dict)

    def test_dot_notation(self, UserWithinAddresses):
        norm = UserWithinAddresses.vars(excludes=[
            'addresses.suburb',
            'addresses.state'
        ])

        assert "addresses" in norm
        assert isinstance(norm["addresses"], list)
        assert len(norm["addresses"]) == len(UserWithinAddresses.addresses)

        assert "street" in norm["addresses"][0]
        assert "country" in norm["addresses"][0]
        assert "postcode" in norm["addresses"][0]
        assert "suburb" not in norm["addresses"][0]
        assert "state" not in norm["addresses"][0]

    def test_dot_notation_not_exists(self, UserWithinAddresses):
        with pytest.raises(AttributeError):
            norm = UserWithinAddresses.vars(excludes=[
                'primary_address.suburb',
                'primary_address.state'
            ])

    def test_dot_notation_complex(self, UserWithinAddresses):
        norm = UserWithinAddresses.vars(
            includes=['primary_address'],
            excludes=[
                'primary_address.suburb',
                'primary_address.state'
            ]
        )

        assert "primary_address" in norm
        assert isinstance(norm["primary_address"], dict)

        assert "street" in norm["primary_address"]
        assert "country" in norm["primary_address"]
        assert "postcode" in norm["primary_address"]
        assert "suburb" not in norm["primary_address"]
        assert "state" not in norm["primary_address"]
