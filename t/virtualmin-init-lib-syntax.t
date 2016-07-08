use Test::Strict tests => 3;                      # last test to print

syntax_ok( 'virtualmin-init-lib.pl' );
strict_ok( 'virtualmin-init-lib.pl' );
warnings_ok( 'virtualmin-init-lib.pl' );
