import sys, unittest
import continuity_db_helper


class TDD_ShowRoutesTests(unittest.TestCase):
    def test_parser_has_show_routes(self):
        p = continuity_db_helper.parser()
        # Check subparser exists
        subnames = [action.dest for action in p._subparsers._group_actions if hasattr(action, 'choices')]
        # Alternative: just try parsing show-routes
        args = p.parse_args(["--db", "continuity.db", "show-routes", "%"])
        self.assertTrue(hasattr(args, 'func'))

    def test_show_routes_finds_entries(self):
        p = continuity_db_helper.parser()
        args = p.parse_args(["--db", "continuity.db", "show-routes", "%ethics%"])
        # Should not raise
        args.func(args)


if __name__ == "__main__":
    unittest.main()