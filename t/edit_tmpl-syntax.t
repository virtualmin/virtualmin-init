use Test::Strict tests => 3;                      # last test to print

syntax_ok( 'edit_tmpl.cgi' );
strict_ok( 'edit_tmpl.cgi' );
warnings_ok( 'edit_tmpl.cgi' );
