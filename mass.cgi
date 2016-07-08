#!/usr/local/bin/perl
# Start, stop or delete multiple actions
use strict;
use warnings;
our (%text, %in);

require './virtualmin-init-lib.pl';
&ReadParse();
my @d = split(/\0/, $in{'d'});
@d || &error($text{'mass_enone'});

# Get the actions
my @dominits;
foreach my $di (@d) {
	my ($did, $name) = split(/\//, $di);
	my $d = &virtual_server::get_domain($did);
	my ($init) = grep { $_->{'name'} eq $name } &list_domain_actions($d);
	if ($d && $init) {
		push(@dominits, [ $d, $init ]);
		}
	}

my $idx = "index.cgi?dom=$dominits[0]->[0]->{'id'}";
if ($in{'delete'}) {
	# Delete them all
	foreach my $di (@dominits) {
		&delete_domain_action($di->[0], $di->[1]);
		}
	&redirect($idx);
	}
elsif ($in{'startnow'}) {
	# Start them in series
	&ui_print_unbuffered_header(undef, $text{'start_titles'}, "");

	foreach my $di (@dominits) {
		print &text('start_starting',
			    "<tt>$di->[1]->{'name'}</tt>"),"\n";
		print "<pre>";
		&start_domain_action($di->[0], $di->[1]);
		print "</pre>";
		}

	&ui_print_footer($idx, $text{'index_return'});
	}
elsif ($in{'stopnow'}) {
	# Stop them in series
	&ui_print_unbuffered_header(undef, $text{'stop_titles'}, "");

	foreach my $di (@dominits) {
		print &text('stop_stopping',
			    "<tt>$di->[1]->{'name'}</tt>"),"\n";
		print "<pre>";
		&stop_domain_action($di->[0], $di->[1]);
		print "</pre>";
		}

	&ui_print_footer($idx, $text{'index_return'});
	}
elsif ($in{'restartnow'}) {
	# Restart them in series
	&ui_print_unbuffered_header(undef, $text{'restart_titles'}, "");

	foreach my $di (@dominits) {
		print &text('restart_restarting',
			    "<tt>$di->[1]->{'name'}</tt>"),"\n";
		print "<pre>";
		&restart_domain_action($di->[0], $di->[1]);
		print "</pre>";
		}

	&ui_print_footer($idx, $text{'index_return'});
	}
else {
	&error("No button clicked!");
	}
