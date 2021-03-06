#!/usr/local/bin/perl
# Show a page for creating or editing a bootup action associated with
# some domain.
use strict;
use warnings;
our (%text, %in, %config);
our $module_name;

require './virtualmin-init-lib.pl';
&ReadParse();
my $d = $in{'dom'} ? &virtual_server::get_domain($in{'dom'}) : undef;
&ui_print_header($d ? &virtual_server::domain_in($d) : undef,
		 $in{'new'} ? $text{'edit_title1'} : $text{'edit_title2'}, "");

my $init;
my $tmpl;
if (!$in{'new'}) {
	# Get the existing action
	($init) = grep { $_->{'id'} eq $in{'id'} }
		       &list_domain_actions($d);
	$init || &error($text{'edit_egone'});
	}
else {
	# Adding a new action
	$init = { 'status' => 1 };
	($tmpl) = grep { $_->{'id'} eq $in{'tmpl'} } &list_action_templates();
	if ($config{'mode'} eq 'smf' && !$tmpl) {
		$init->{'stop'} = ':kill';
		}
	}

print &ui_form_start("save.cgi", "post");
print &ui_hidden("new", $in{'new'});
print &ui_hidden("tmpl", $in{'tmpl'});
print &ui_hidden("id", $in{'id'});
if ($in{'dom'}) {
	print &ui_hidden("dom", $in{'dom'});
	}
print &ui_table_start($text{'edit_header'}, undef, 2);

# Domain selector, if needed
if (!$in{'dom'}) {
	my @doms = grep { $_->{$module_name} &&
		       &virtual_server::can_edit_domain($_) }
		     &virtual_server::list_domains();
	print &ui_table_row($text{'edit_dom'},
		&ui_select("dom", undef,
			[ map { [ $_->{'id'}, $_->{'dom'} ] } @doms ]));
	}

# Action name
print &ui_table_row($text{'edit_name'},
	&ui_textbox("name", $init->{'name'}, 30));

# Description
print &ui_table_row($text{'edit_desc'},
	&ui_textbox("desc", $init->{'desc'}, 60));

# Enabled?
if (&can_start_actions()) {
	# Init mode, in which we can just control if started at boot
	print &ui_table_row($text{'edit_status'},
		&ui_yesno_radio("status", int($init->{'status'})));
	}
else {
	# SMF mode, in which we can see the real status
	my @opts = ( [ 1, $text{'yes'} ],
		     [ 0, $text{'no'} ] );
	if ($init->{'status'} == 2) {
		push(@opts, [ 2, $text{'edit_maint'} ]);
		}
	print &ui_table_row($text{'edit_status2'},
			    &ui_radio("status", $init->{'status'}, \@opts));
	if ($init->{'status'} == 2) {
		# Show failure log
		print &ui_table_row($text{'edit_startlog'},
			"<pre>".&html_escape($init->{'startlog'})."</pre>");
		}
	}

if ($tmpl) {
	# Adding from template .. show name
	print &ui_table_row($text{'edit_tmpl'}, $tmpl->{'desc'});

	# Show parameters
	for(my $i=0; defined($tmpl->{'pname_'.$i}); $i++) {
		my $tt = $tmpl->{'ptype_'.$i};
		my $tn = 'param_'.$tmpl->{'pname_'.$i};
		my $of = $tmpl->{'popts_'.$i};
		my @opts = $of ? &read_opts_file($of) : ( );
		print &ui_table_row($tmpl->{'pdesc_'.$i},
			$tt == 0 ? &ui_textbox($tn, undef, 50) :
			$tt == 1 ? &ui_textbox($tn, undef, 10) :
			$tt == 2 ? &ui_textbox($tn, undef, 50).
				    &file_chooser_button($tn) :
			$tt == 3 ? &ui_radio($tn, $opts[0]->[0], \@opts) :
			$tt == 4 ? &ui_select($tn, $opts[0]->[0], \@opts) :
				   undef);
		}

	# Show fixed code for start and stop
	my $start = $tmpl->{'start'};
	$start = &substitute_template($start, $d) if ($d);
	print &ui_table_row($text{'edit_start'},
			    "<pre>".&html_escape($start)."</pre>");

	my $stop = $tmpl->{'stop'};
	$stop = &substitute_template($stop, $d) if ($d);
	print &ui_table_row($text{'edit_stop'},
			    $stop eq ":kill" ? $text{'edit_stopkill'} :
				    "<pre>".&html_escape($stop)."</pre>");
	}
else {
	# Start code
	print &ui_table_row($text{'edit_start'},
		&ui_textarea("start", $init->{'start'}, 5, 80));

	# Stop code
	my $stopdef;
	if ($config{'mode'} eq 'smf') {
		$stopdef = &ui_radio(
			     "stop_def", $init->{'stop'} eq ':kill' ? 1 : 0,
			     [ [ 1, $text{'edit_stopkill'} ],
			       [ 0, $text{'edit_stopbelow'} ] ])."<br>\n";
		}
	print &ui_table_row($text{'edit_stop'},
		$stopdef.
		&ui_textarea("stop", $init->{'stop'} eq ':kill' ? undef :
					$init->{'stop'}, 5, 80));

	# Current processes
	if (!$in{'new'}) {
		my @procs = &get_started_processes($init);
		if (@procs) {
			my @table = ( );
			foreach my $p (@procs) {
				push(@table, [ $p->{'pid'}, $p->{'cpu'},
					       $p->{'size'}, $p->{'args'} ]);
				}
			print &ui_table_row($text{'edit_procs'},
				&ui_columns_table(
				  [ $text{'edit_ppid'}, $text{'edit_pcpu'},
				    $text{'edit_psize'}, $text{'edit_pcmd'} ],
				  undef,
				  \@table));
			}
		}
	}

# SMF FMRI
if (!$in{'new'} && $init->{'fmri'}) {
	print &ui_table_row($text{'edit_fmri'},
			    "<tt>".&html_escape($init->{'fmri'})."</tt>");
	}

print &ui_table_end();
if ($in{'new'}) {
	print &ui_form_end([ [ "create", $text{'create'} ] ]);
	}
else {
	print &ui_form_end([ [ "save", $text{'save'} ],
			     [ "delete", $text{'delete'} ],
			     undef,
			     &can_start_actions() ? (
				     [ "startnow", $text{'edit_startnow'} ],
				     [ "stopnow", $text{'edit_stopnow'} ]
				     ) : ( )
			   ]);
	}

&ui_print_footer("index.cgi?dom=$in{'dom'}", $text{'index_return'});
