#!/usr/local/bin/perl
# Show a list of bootup scripts that the user already has configured

require './virtualmin-init-lib.pl';
&ReadParse();
$d = $in{'dom'} ? &virtual_server::get_domain($in{'dom'}) : undef;
&ui_print_header($d ? &virtual_server::domain_in($d) : undef,
		 $text{'index_title'}, "", undef, 0, 1);
@templates = &list_action_templates();

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
	$many = 1;
	}

# Show existing init scripts for all domains
foreach my $d (@doms) {
	foreach my $i (&list_domain_actions($d)) {
		$i->{'dom'} = $d->{'id'};
		$i->{'domname'} = $d->{'dom'};
		push(@allinits, $i);
		}
	}

# Work out limit
if ($access{'max'}) {
	$c = &count_user_actions();
	if ($c >= $access{'max'}) {
		print "<b>",&text('index_hitmax', $access{'max'}),"</b><p>\n";
		$no_create = 1;
		}
	elsif ($c) {
		print "<b>",&text('index_max', $c, $access{'max'}),"</b><p>\n";
		}
	else {
		print "<b>",&text('index_max2', $access{'max'}),"</b><p>\n";
		}
	}

if (!$no_create) {
	@links = ( "<a href='edit.cgi?new=1&dom=$in{'dom'}'>".
		   "$text{'index_add'}</a>" );
	foreach $tmpl (@templates) {
		push(@links, "<a href='edit.cgi?new=1&dom=$in{'dom'}&".
			     "tmpl=$tmpl->{'id'}'>".
			     &text('index_add2', $tmpl->{'desc'})."</a>");
		}
	}
if (@allinits) {
	unshift(@links, &select_all_link("d"), &select_invert_link("d"));
	@tds = ( "width=5", $many ? ( undef ) : ( ), undef, undef, "width=10%");
	print &ui_form_start("mass.cgi", "post");
	print &ui_links_row(\@links);
	print &ui_columns_start([ "",
				  $text{'index_name'},
				  $many ? ( $text{'index_dom'} ) : ( ),
				  $text{'index_desc'},
				  &can_start_actions() ? $text{'index_status'}
						       : $text{'index_status2'}
				 ], 100, 0, \@tds);
	$green = "<font color=#00aa00>$text{'yes'}</font>";
	$red = "<font color=#ff0000>$text{'no'}</font>";
	$orange = "<font color=#ffaa00>$text{'index_maint'}</font>";
	foreach my $i (@allinits) {
		print &ui_checked_columns_row([
			"<a href='edit.cgi?name=$i->{'name'}&dom=$i->{'dom'}'>".
			 "$i->{'name'}</a>",
			$many ? ( $i->{'domname'} ) : ( ),
			$i->{'desc'},
			$i->{'status'} == 1 ? $green :
			$i->{'status'} == 2 ? $orange :
					      $red
			],
			\@tds, "d", $i->{'dom'}."/".$i->{'name'});
		}
	print &ui_columns_end();
	print &ui_links_row(\@links);
	print &ui_form_end([ [ "delete", $text{'index_delete'} ],
			     undef,
			     &can_start_actions() ? (
				     [ "startnow", $text{'index_startnow'} ],
				     [ "stopnow", $text{'index_stopnow'} ]
				     ) : ( ),
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

# Show list of templates
if ($access{'templates'}) {
	print "<hr>\n";
	print $text{'index_tdesc2'},"<p>\n";
	@links = ( "<a href='edit_tmpl.cgi?new=1'>$text{'index_tadd'}</a>" );
	if (@templates) {
		print &ui_links_row(\@links);
		print &ui_columns_start([ $text{'index_tdesc'},
					  $text{'index_tstart'},
					  $text{'index_tstop'} ]);
		foreach $t (@templates) {
			print &ui_columns_row([
				"<a href='edit_tmpl.cgi?id=$t->{'id'}'>".
				"$t->{'desc'}</a>",
				&shorten_command($t->{'start'}),
				&shorten_command($t->{'stop'}),
				]);
			}
		print &ui_columns_end();
		print &ui_links_row(\@links);
		}
	else {
		print "<b>$text{'index_tnone'}</b><p>\n";
		print &ui_links_row(\@links);
		}
	}

&ui_print_footer("/", $text{'index'});

sub shorten_command
{
local ($cmd) = @_;
$cmd =~ s/\n/ ; /g;
if (length($cmd) > 60) {
	$cmd = substr($cmd, 0, 60)." ...";
	}
return &html_escape($cmd);
}
