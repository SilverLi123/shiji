"""Binding the LAN listener must work without name resolution."""
import unittest
from unittest.mock import patch
from sync_transport import TLSServer,SyncHandler

class ListenerTests(unittest.TestCase):
 def test_bind_does_not_wait_for_reverse_dns(self):
  with patch('socket.getfqdn',side_effect=AssertionError('DNS must not be needed')):
   server=TLSServer(('127.0.0.1',0),SyncHandler)
   try:
    self.assertGreater(server.server_port,0)
    self.assertEqual(server.server_address[0],'127.0.0.1')
   finally:server.server_close()
