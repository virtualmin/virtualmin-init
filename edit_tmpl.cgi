#!/usr/local/bin/perl
# Show a page for creating or editing an action template

require './virtualmin-init-lib.pl';
&ReadParse();
$access{'templates'} || &error($text{'tmpl_ecannot'});
&ui_print_header(undef,
		 $in{'new'} ? $text{'tmpl_title1'} : $text{'tmpl_title2'}, "");

if (!$in{'new'}) {
	# Get the existing template
	($tmpl) = grep { $_->{'id'} == $in{'id'} } &list_action_templates();
	}

print &ui_form_start("save_tmpl.cgi", "post");
print &ui_hidden("new", $in{'new'});
print &ui_hidden("id", $in{'id'});
print &ui_table_start($text{'tmpl_header'}, undef, 2);

# Description
print &ui_table_row($text{'tmpl_desc'},
	&ui_textbox("desc", $tmpl->{'desc'}, 60));

# Start code
print &ui_table_row($text{'edit_start'},
	&ui_textarea("start", $tmpl->{'start'}, 5, 80));

# Stop code
if ($config{'mode'} eq 'smf') {
	$stopdef = &ui_radio("stop_def", $tmpl->{'stop'} eq ':kill' ? 1 : 0,
			     [ [ 1, $text{'edit_stopkill'} ],
			       [ 0, $text{'edit_stopbelow'} ] ])."<br>\n";
	}
print &ui_table_row($text{'edit_stop'},
	$stopdef.
	&ui_textarea("stop", $tmpl->{'stop'} eq ':kill' ? undef :
				$tmpl->{'stop'}, 5, 80));

# XML template
if ($config{'mode'} eq 'smf') {
	print &ui_table_row($text{'tmpl_xml'},
		&ui_radio("xml_def", $tmpl->{'xml'} ? 0 : 1,
			  [ [ 1, $text{'tmpl_xmldef'} ],
			    [ 0, $text{'tmpl_xmlbelow'} ] ])."<br>\n".
		&ui_textarea("xml", $tmpl->{'xml'}, 10, 80));
	}

print &ui_table_end();

# Section for additional parameters
print &ui_table_start($text{'tmpl_header2'}, undef, 2);

$ptable = &ui_columns_start([ $text{'tmpl_pname'},
			      $text{'tmpl_ptype'},
			      $text{'tmpl_pdesc'} ], 100);
for($pmax=0; defined($tmpl->{'pname_'.$pmax}); $pmax++) { }
for($i=0; $i < $pmax+3; $i++) {
	$ptable .= &ui_columns_row([
		&ui_textbox("pname_$i", $tmpl->{'pname_'.$i}, 10),
		&ui_select("ptype_$i", $tmpl->{'ptype_'.$i},
			   [ [ 0, $text{'tmpl_ptype0'} ],
			     [ 1, $text{'tmpl_ptype1'} ],
			     [ 2, $text{'tmpl_ptype2'} ],
			   ]),
		&ui_textbox("pdesc_$i", $tmpl->{'pdesc_'.$i}, 50),
		]);
	}
$ptable .= &ui_columns_end();
print &ui_table_row(undef, $ptable, 2);

print &ui_table_end();
if ($in{'new'}) {
	print &ui_form_end([ [ "create", $text{'create'} ] ]);
	}
else {
	print &ui_form_end([ [ "save", $text{'save'} ],
			     [ "delete", $text{'delete'} ] ]);
	}

&ui_print_footer("", $text{'index_return'});


