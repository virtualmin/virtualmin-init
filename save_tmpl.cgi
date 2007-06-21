#!/usr/local/bin/perl
# Create, update or delete some action template

require './virtualmin-init-lib.pl';
&ReadParse();
$access{'templates'} || &error($text{'tmpl_ecannot'});

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
	$in{'stop'} =~ s/\r//g;
	$tmpl->{'stop'} = $in{'stop'};
	if ($in{'xml_def'}) {
		delete($tmpl->{'xml'});
		}
	else {
		$in{'xml'} =~ s/\r//g;
		$in{'xml'} =~ /\S/ || &error($text{'tmpl_exml'});
		$tmpl->{'xml'} = $in{'xml'};
		}

	# Validate user-definable parameters
	for($i=0; defined($tmpl->{'pname_'.$i}); $i++) {
		delete($tmpl->{'pname_'.$i});
		delete($tmpl->{'ptype_'.$i});
		delete($tmpl->{'pdesc_'.$i});
		}
	for($i=0; defined($in{'pname_'.$i}); $i++) {
		next if (!$in{'pname_'.$i});
		$in{'pname_'.$i} =~ /^[a-z0-9_]+$/i ||
			&error(&text('tmpl_epname', $i+1));
		$tmpl->{'pname_'.$i} = $in{'pname_'.$i};
		$tmpl->{'ptype_'.$i} = $in{'ptype_'.$i};
		$in{'pdesc_'.$i} =~ /\S/ ||
			&error(&text('tmpl_epdesc', $i+1));
		$tmpl->{'pdesc_'.$i} = $in{'pdesc_'.$i};
		}

	# Create or save
	&save_action_template($tmpl);
	&redirect("");
	}
