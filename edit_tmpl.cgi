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
print &ui_table_row($text{'edit_stop'},
	&ui_textarea("stop", $tmpl->{'stop'}, 5, 80));

print &ui_table_end();
if ($in{'new'}) {
	print &ui_form_end([ [ "create", $text{'create'} ] ]);
	}
else {
	print &ui_form_end([ [ "save", $text{'save'} ],
			     [ "delete", $text{'delete'} ] ]);
	}

&ui_print_footer("", $text{'index_return'});


