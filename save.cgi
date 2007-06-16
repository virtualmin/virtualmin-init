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
	$init->{'desc'} = $in{'desc'};
	$init->{'status'} = $in{'status'};
	$in{'start'} =~ s/\r//g;
	$in{'start'} =~ s/\n+$//g;
	$in{'start'} .= "\n";
	$in{'start'} =~ /\S/ || &error($text{'save_estart'});
	$init->{'start'} = $in{'start'};
	$in{'stop'} =~ s/\r//g;
	$in{'stop'} =~ s/\n+$//g;
	$in{'stop'} .= "\n" if ($in{'stop'} =~ /\S/);
	$init->{'stop'} = $in{'stop'};
	$init->{'user'} = $d->{'user'};

	# Create or save
	if ($in{'new'}) {
		&create_domain_action($d, $init);
		}
	else {
		&modify_domain_action($d, $d, $init, $oldinit);
		}
	&redirect("index.cgi?dom=$in{'dom'}");
	}

