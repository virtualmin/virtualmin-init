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
	$init = { 'status' => 1 };
	}

print &ui_form_start("save.cgi", "post");
print &ui_hidden("new", $in{'new'});
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
print &ui_table_row($text{'edit_status'},
	&ui_yesno_radio("status", int($init->{'status'})));

# Template, if any are available
@tmpls = &list_action_templates();
print "<script>\n";
print "function select_template(id)\n";
print "{\n";
print "form = document.forms[0]\n";
print "if (id == 0) {\n";
print "  form.start.value = '';\n";
print "  form.start.disabled = false;\n";
print "  form.stop.value = '';\n";
print "  form.stop.disabled = false;\n";
print "  }\n";
foreach $tmpl (@tmpls) {
	print "else if (id == $tmpl->{'id'}) {\n";
	$tmpl->{'start'} =~ s/\n/\\n/g;
	$tmpl->{'stop'} =~ s/\n/\\n/g;
	print "  form.start.value = '$tmpl->{'start'}';\n";
	print "  form.start.disabled = true;\n";
	print "  form.stop.value = '$tmpl->{'stop'}';\n";
	print "  form.stop.disabled = true;\n";
	print "  }\n";
	}
print "}\n";
print "</script>\n";
if ($in{'new'} && @tmpls) {
	print &ui_table_row($text{'edit_tmpl'},
		&ui_select("tmpl", 0,
		  [ [ 0, "&lt;$text{'edit_manual'}&gt;" ],
		    map { [ $_->{'id'}, $_->{'desc'} ] } @tmpls ],
		  1, 0, 0, 0,
		  "onChange='select_template(options[selectedIndex].value)'"));
	}

# Start code
print &ui_table_row($text{'edit_start'},
	&ui_textarea("start", $init->{'start'}, 5, 80));

# Stop code
print &ui_table_row($text{'edit_stop'},
	&ui_textarea("stop", $init->{'stop'}, 5, 80));

print &ui_table_end();
if ($in{'new'}) {
	print &ui_form_end([ [ "create", $text{'create'} ] ]);
	}
else {
	print &ui_form_end([ [ "save", $text{'save'} ],
			     [ "delete", $text{'delete'} ],
			     undef,
			     [ "startnow", $text{'edit_startnow'} ],
			     [ "stopnow", $text{'edit_stopnow'} ] ]);
	}

&ui_print_footer("index.cgi?dom=$in{'dom'}", $text{'index_return'});


