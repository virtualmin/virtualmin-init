#!/usr/local/bin/perl
# Start, stop or delete multiple actions

require './virtualmin-init-lib.pl';
&ReadParse();
@d = split(/\0/, $in{'d'});
@d || &error($text{'mass_enone'});

# Get the actions
foreach $di (@d) {
	($did, $name) = split(/\//, $di);
	local $d = &virtual_server::get_domain($did);
	local ($init) = grep { $_->{'name'} eq $name } &list_domain_actions($d);
	if ($d && $init) {
		push(@dominits, [ $d, $init ]);
		}
	}

$idx = "index.cgi?dom=$dominits[0]->[0]->{'id'}";
if ($in{'delete'}) {
	# Delete them all
	foreach $di (@dominits) {
		&delete_domain_action($di->[0], $di->[1]);
		}
	&redirect($idx);
	}
elsif ($in{'startnow'}) {
	# Start them in series
	&ui_print_unbuffered_header(undef, $text{'start_titles'}, "");

	foreach $di (@dominits) {
		print &text('start_starting',
			    "<tt>$di->[1]->{'name'}</tt>"),"\n";
		print "<pre>";
		$ex = &start_domain_action($di->[0], $di->[1]);
		print "</pre>";
		}

	&ui_print_footer($idx, $text{'index_return'});
	}
elsif ($in{'stopnow'}) {
	# Stop them in series
	&ui_print_unbuffered_header(undef, $text{'stop_titles'}, "");

	foreach $di (@dominits) {
		print &text('stop_stoping',
			    "<tt>$di->[1]->{'name'}</tt>"),"\n";
		print "<pre>";
		$ex = &stop_domain_action($di->[0], $di->[1]);
		print "</pre>";
		}

	&ui_print_footer($idx, $text{'index_return'});
	}
else {
	&error("No button clicked!");
	}

