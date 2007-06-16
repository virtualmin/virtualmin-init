#!/usr/local/bin/perl
# Show a list of bootup scripts that the user already has configured

require './virtualmin-init-lib.pl';
&ReadParse();
$d = $in{'dom'} ? &virtual_server::get_domain($in{'dom'}) : undef;
&ui_print_header($d ? &virtual_server::domain_in($d) : undef,
		 $text{'index_title'}, "", undef, 0, 1);

# Work out domains to work on
if ($d) {
	# Just one
	@doms = ( $d );
	}
else {
	# All domains for the user
	@doms = grep { $_->{$module_name} &&
		       &virtual_server::can_edit_domain($_) }
		     &virtual_server::list_domains();
	}

# Show existing init scripts for all domains
foreach my $d (@doms) {
	foreach my $i (&list_domain_actions($d)) {
		$i->{'dom'} = $d->{'id'};
		push(@allinits, $i);
		}
	}
@links = ( "<a href='edit.cgi?new=1&dom=$in{'dom'}'>$text{'index_add'}</a>" );
if (@allinits) {
	unshift(@links, &select_all_link("d"), &select_invert_link("d"));
	@tds = ( "width=5", undef, undef, "width=10%" );
	print &ui_form_start("mass.cgi", "post");
	print &ui_links_row(\@links);
	print &ui_columns_start([ "",
				  $text{'index_name'},
				  $text{'index_desc'},
				  $text{'index_status'} ], 100, 0, \@tds);
	$green = "<font color=#00aa00>$text{'yes'}</font>";
	$red = "<font color=#ff0000>$text{'no'}</font>";
	foreach my $i (@allinits) {
		print &ui_checked_columns_row([
			"<a href='edit.cgi?name=$i->{'name'}&dom=$i->{'dom'}'>".
			 "$i->{'name'}</a>",
			$i->{'desc'},
			$i->{'status'} ? $green : $red ],
			\@tds, "d", $i->{'dom'}."/".$i->{'name'});
		}
	print &ui_columns_end();
	print &ui_links_row(\@links);
	print &ui_form_end([ [ "delete", $text{'index_delete'} ],
			     undef,
			     [ "startnow", $text{'index_startnow'} ],
			     [ "stopnow", $text{'index_stopnow'} ],
			   ]);
	}
else {
	if ($in{'dom'}) {
		print "<b>$text{'index_none'}</b><p>\n";
		}
	else {
		print "<b>$text{'index_none2'}</b><p>\n";
		}
	print &ui_links_row(\@links);
	}

&ui_print_footer("/", $text{'index'});

