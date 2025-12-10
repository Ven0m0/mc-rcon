# -*- coding: utf-8 -*-
"""
Exposes the core RCON client classes.
"""

from mcrconpy.core import Rcon, AsyncRcon, Packet

# Legacy alias for backward compatibility if needed,
# though user asked to consolidate, 'RconPy' was the old controller class name.
# Mapping RconPy to Rcon (Sync) makes sense.
RconPy = Rcon
