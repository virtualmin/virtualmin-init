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

	# Create or save
	&save_action_template($tmpl);
	&redirect("");
	}

