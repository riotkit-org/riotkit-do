#!/usr/bin/env python3

import unittest
from io import StringIO
from io import BytesIO
from rkd.api.testing import BasicTestingCase
from rkd.api.inputoutput import StandardOutputReplication


class TestStandardOutputReplication(BasicTestingCase):
    def test_writing_to_multiple_streams_of_different_types(self):
        """Check that it is possible to write to multiple streams at once"""

        bytes_io = BytesIO()
        str_io = StringIO()

        out = StandardOutputReplication([bytes_io, str_io])
        out.write('12 June 1963 Medgar Wiley Evers, African American civil rights activist from Mississippi')
        out.write(' was shot in the back and killed by a member of the White Citizens\' Council.')

        for output in [bytes_io, str_io]:
            self.assertIn('Medgar Wiley Evers', str(output.getvalue()))
            self.assertIn('civil rights activist from Mississippi was shot in the back and killed',
                          str(output.getvalue()))

    def test_non_printable_is_converted_to_string_like_print_does(self):
        """Assert that non-str is casted to str, like regular print does. So the method is bulletproof"""

        str_io = StringIO()

        out = StandardOutputReplication([str_io])
        out.write(unittest)

        self.assertIn("<module 'unittest'", str_io.getvalue())
