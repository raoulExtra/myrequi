import sys, unittest
import helper_for_db


class TDD_ShowRoutesTests(unittest.TestCase):
    def test_parser_has_show_routes(self):
        p = helper_for_db.parser()
        # Check subparser exists
        subnames = [action.dest for action in p._subparsers._group_actions if hasattr(action, 'choices')]
        # Alternative: just try parsing show-routes
        args = p.parse_args(["--db", "continuity.db", "show-routes", "%"])
        self.assertTrue(hasattr(args, 'func'))

    def test_show_routes_finds_entries(self):
        p = helper_for_db.parser()
        args = p.parse_args(["--db", "continuity.db", "show-routes", "%ethics%"])
        # Should not raise
        args.func(args)


if __name__ == "__main__":
    unittest.main()