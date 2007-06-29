#!/usr/local/bin/perl
# Show a page for creating or editing a bootup action associated with
# some domain.

require './virtualmin-init-lib.pl';
&ReadParse();
$d = $in{'dom'} ? &virtual_server::get_domain($in{'dom'}) : undef;
&ui_print_header($d ? &virtual_server::domain_in($d) : undef,
		 $in{'new'} ? $text{'edit_title1'} : $text{'edit_title2'}, "");

if (!$in{'new'}) {
	# Get the existing action
	($init) = grep { $_->{'name'} eq $in{'name'} } 
		       &list_domain_actions($d);
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
print &ui_hidden("old", $in{'name'});
if ($in{'dom'}) {
	print &ui_hidden("dom", $in{'dom'});
	}
print &ui_table_start($text{'edit_header'}, undef, 2);

# Domain selector, if needed
if (!$in{'dom'}) {
	@doms = grep { $_->{$module_name} &&
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
	for($i=0; defined($tmpl->{'pname_'.$i}); $i++) {
		$tt = $tmpl->{'ptype_'.$i};
		$tn = 'param_'.$tmpl->{'pname_'.$i};
		print &ui_table_row($tmpl->{'pdesc_'.$i},
			$tt == 0 ? &ui_textbox($tn, undef, 50) :
			$tt == 1 ? &ui_textbox($tn, undef, 10) : undef);
		}

	# Show fixed code for start and stop
	$start = $tmpl->{'start'};
	$start = &substitute_template($start, $d) if ($d);
	print &ui_table_row($text{'edit_start'},
			    "<pre>".&html_escape($start)."</pre>");

	$stop = $tmpl->{'stop'};
	$stop = &substitute_template($stop, $d) if ($d);
	print &ui_table_row($text{'edit_stop'},
			    "<pre>".&html_escape($stop)."</pre>");
	}
else {
	# Start code
	print &ui_table_row($text{'edit_start'},
		&ui_textarea("start", $init->{'start'}, 5, 80));

	# Stop code
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


