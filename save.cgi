#!/usr/local/bin/perl
# Create, update, delete, start or stop some action

require './virtualmin-init-lib.pl';
&ReadParse();
$d = &virtual_server::get_domain($in{'dom'});
&virtual_server::can_edit_domain($d) || &error($text{'save_ecannot'});

# Get the current boot action
@inits = &list_domain_actions($d);
if ($in{'old'}) {
	($init) = grep { $_->{'name'} eq $in{'old'} } @inits;
	$oldinit = { %$init };
	}
elsif ($access{'max'}) {
	# Check if limit was hit
	$c = &count_user_actions();
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
		($clash) = grep { $_->{'name'} eq $in{'name'} } @inits;
		$clash && &error($text{'save_eclash'});
		}
	$init->{'name'} = $in{'name'};
	$in{'desc'} =~ /\S/ || &error($text{'save_edesc'});
	$init->{'desc'} = $in{'desc'};
	$init->{'status'} = $in{'status'};
	if ($in{'new'} && $in{'tmpl'}) {
		# From template
		($tmpl) = grep { $_->{'id'} == $in{'tmpl'} }
				&list_action_templates();
		%thash = %$d;
		for($i=0; defined($tmpl->{'pname_'.$i}); $i++) {
			$td = $tmpl->{'pdesc_'.$i};
			$tt = $tmpl->{'ptype_'.$i};
			$tn = $tmpl->{'pname_'.$i};
			$tv = $in{'param_'.$tn};
			if ($tt == 0 || $tt == 2) {
				$tv =~ /\S/ ||
					&error(&text('save_eptype0', $td));
				$thash{$tn} = $tv;
				}
			elsif ($tt == 1) {
				$tv =~ /^\d+$/ ||
					&error(&text('save_eptype1', $td));
				$thash{$tn} = $tv;
				}
			}
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
		&create_domain_action($d, $init, $tmpl);
		}
	else {
		&modify_domain_action($d, $d, $init, $oldinit);
		}
	&redirect("index.cgi?dom=$in{'dom'}");
	}

