use Test::Strict tests => 3;                      # last test to print

syntax_ok( 'save_tmpl.cgi' );
strict_ok( 'save_tmpl.cgi' );
warnings_ok( 'save_tmpl.cgi' );
