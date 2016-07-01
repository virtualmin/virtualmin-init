#!/usr/local/bin/perl
# Create, update or delete some action template
use strict;
use warnings;
our (%access, %text, %in, %config);

require './virtualmin-init-lib.pl';
&ReadParse();
$access{'templates'} || &error($text{'tmpl_ecannot'});

my $tmpl;
if (!$in{'new'}) {
	# Get the existing template
	($tmpl) = grep { $_->{'id'} == $in{'id'} } &list_action_templates();
	}

if ($in{'delete'}) {
	# Just remove the action
	&delete_action_template($tmpl);
	&redirect("");
	}
else {
	# Validate inputs
	&error_setup($text{'tmpl_err'});
	$in{'desc'} =~ /\S/ || &error($text{'tmpl_edesc'});
	$tmpl->{'desc'} = $in{'desc'};
	$in{'start'} =~ s/\r//g;
	$in{'start'} =~ /\S/ || &error($text{'tmpl_estart'});
	$tmpl->{'start'} = $in{'start'};
	if ($in{'stop_def'}) {
		$tmpl->{'stop'} = ':kill';
		}
	else {
		$in{'stop'} =~ s/\r//g;
		$tmpl->{'stop'} = $in{'stop'};
		}
	if ($in{'xml_def'} || $config{'mode'} ne 'smf') {
		delete($tmpl->{'xml'});
		}
	else {
		$in{'xml'} =~ s/\r//g;
		$in{'xml'} =~ /\S/ || &error($text{'tmpl_exml'});
		$tmpl->{'xml'} = $in{'xml'};
		}

	# Validate user-definable parameters
	for(my $i=0; defined($tmpl->{'pname_'.$i}); $i++) {
		delete($tmpl->{'pname_'.$i});
		delete($tmpl->{'ptype_'.$i});
		delete($tmpl->{'pdesc_'.$i});
		}
	for(my $i=0; defined($in{'pname_'.$i}); $i++) {
		next if (!$in{'pname_'.$i});
		$in{'pname_'.$i} =~ /^[a-z0-9_]+$/i ||
			&error(&text('tmpl_epname', $i+1));
		$tmpl->{'pname_'.$i} = $in{'pname_'.$i};
		$tmpl->{'ptype_'.$i} = $in{'ptype_'.$i};
		$in{'pdesc_'.$i} =~ /\S/ ||
			&error(&text('tmpl_epdesc', $i+1));
		$tmpl->{'pdesc_'.$i} = $in{'pdesc_'.$i};
		if ($tmpl->{'ptype_'.$i} == 3 || $tmpl->{'ptype_'.$i} == 4) {
			-r $in{'popts_'.$i} ||
				&error(&text('tmpl_epopts', $i+1));
			$tmpl->{'popts_'.$i} = $in{'popts_'.$i};
			}
		else {
			delete($tmpl->{'popts_'.$i});
			}
		}

	# Create or save
	&save_action_template($tmpl);
	&redirect("");
	}
