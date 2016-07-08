use Test::Strict tests => 3;                      # last test to print

syntax_ok( 'mass.cgi' );
strict_ok( 'mass.cgi' );
warnings_ok( 'mass.cgi' );
