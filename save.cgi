#!/usr/local/bin/perl
# Create, update, delete, start or stop some action
use strict;
use warnings;
our (%access, %text, %in);

require './virtualmin-init-lib.pl';
&ReadParse();
my $d = &virtual_server::get_domain($in{'dom'});
&virtual_server::can_edit_domain($d) || &error($text{'save_ecannot'});

# Get the current boot action
my @inits = &list_domain_actions($d);
my $init;
my $oldinit;
my $ex; # XXX This is never used, but is captured as a result.
if ($in{'id'}) {
	($init) = grep { $_->{'id'} eq $in{'id'} } @inits;
	$init || &error($text{'edit_egone'});
	$oldinit = { %$init };
	}
elsif ($access{'max'}) {
	# Check if limit was hit
	my $c = &count_user_actions();
	if ($c >= $access{'max'}) {
		&error(&text('save_etoomany', $access{'max'}));
		}
	}

if ($in{'startnow'}) {
	# Start now and show output
	&ui_print_unbuffered_header(&virtual_server::domain_in($d),
				    $text{'start_title'}, "");

	print &text('start_starting', "<tt>$init->{'name'}</tt>"),"\n";
	print "<pre>";
	$ex = &start_domain_action($d, $init);
	print "</pre>";

	&ui_print_footer("index.cgi?dom=$in{'dom'}", $text{'index_return'});
	}
elsif ($in{'stopnow'}) {
	# Stop now and show output
	&ui_print_unbuffered_header(&virtual_server::domain_in($d),
				    $text{'stop_title'}, "");

	print &text('stop_stopping', "<tt>$init->{'name'}</tt>"),"\n";
	print "<pre>";
	$ex = &stop_domain_action($d, $init);
	print "</pre>";

	&ui_print_footer("index.cgi?dom=$in{'dom'}", $text{'index_return'});
	}
elsif ($in{'delete'}) {
	# Just remove the action
	&delete_domain_action($d, $init);
	&redirect("index.cgi?dom=$in{'dom'}");
	}
else {
	# Validate inputs
	&error_setup($text{'save_err'});
	$in{'name'} =~ /^[a-z0-9\.\-\_]+$/i || &error($text{'save_ename'});
	if ($in{'new'} || $in{'name'} ne $init->{'name'}) {
		# Check for clash
		my ($clash) = grep { $_->{'name'} eq $in{'name'} } @inits;
		$clash && &error($text{'save_eclash'});
		}
	$init->{'name'} = $in{'name'};
	$in{'desc'} =~ /\S/ || &error($text{'save_edesc'});
	$init->{'desc'} = $in{'desc'};
	$init->{'status'} = $in{'status'};
	my %tparams;
	my $tmpl;
	if ($in{'new'} && $in{'tmpl'}) {
		# From template
		($tmpl) = grep { $_->{'id'} == $in{'tmpl'} }
				&list_action_templates();
		for(my $i=0; defined($tmpl->{'pname_'.$i}); $i++) {
			my $td = $tmpl->{'pdesc_'.$i};
			my $tt = $tmpl->{'ptype_'.$i};
			my $tn = $tmpl->{'pname_'.$i};
			my $tv = $in{'param_'.$tn};
			if ($tt == 0 || $tt == 2) {
				$tv =~ /\S/ ||
					&error(&text('save_eptype0', $td));
				$tparams{$tn} = $tv;
				}
			elsif ($tt == 1) {
				$tv =~ /^\d+$/ ||
					&error(&text('save_eptype1', $td));
				$tparams{$tn} = $tv;
				}
			elsif ($tt == 3 || $tt == 4) {
				$tparams{$tn} = $tv;
				}
			}
		my %thash = ( %$d, %tparams );
		$thash{'name'} = $init->{'name'};
		$init->{'start'} = &substitute_template(
					$tmpl->{'start'}, \%thash);
		$init->{'stop'} = &substitute_template(
					$tmpl->{'stop'}, \%thash);
		}
	else {
		# Manually entered
		$in{'start'} =~ s/\r//g;
		$in{'start'} =~ /\S/ || &error($text{'save_estart'});
		$init->{'start'} = $in{'start'};
		if ($in{'stop_def'}) {
			$init->{'stop'} = ':kill';
			}
		else {
			$in{'stop'} =~ s/\r//g;
			$init->{'stop'} = $in{'stop'};
			}
		}
	$init->{'start'} =~ s/\n+$//g;
	$init->{'start'} .= "\n";
	$init->{'stop'} =~ s/\n+$//g;
	$init->{'stop'} .= "\n" if ($init->{'stop'} =~ /\S/);
	$init->{'user'} = $d->{'user'};

	# Create or save
	if ($in{'new'}) {
		&create_domain_action($d, $init, $tmpl, \%tparams);
		}
	else {
		&modify_domain_action($d, $d, $init, $oldinit);
		}
	&redirect("index.cgi?dom=$in{'dom'}");
	}
